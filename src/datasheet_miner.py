"""
Datasheet Miner & Pin Extraction Module
========================================
This module queries search engines and cloud LLMs (Gemini Flash) to fetch
datasheet specifications, pinout diagrams, and VCC/GND pin locations for
extracted IC part numbers.
"""

import time
import requests
import json
import re
import urllib.parse
from src.utils import sanitize_json_response

PROMPT_POWER_PINS = """You are an expert component & reverse engineering application engineer.
For the IC or electronic module component '{part_number}' (Package: {package}, Pin Count: {pin_count}), 
identify all VCC (power supply / VBUS / 3.3V / 5V) and GND (ground / 0V) pin numbers or pin labels according to its official datasheet.

Return ONLY a raw JSON object with this exact schema:
{{
  "part_number": "{part_number}",
  "vcc_pins": [1, 8],
  "gnd_pins": [4, 5],
  "vcc_summary": "VCC / VBUS: Pin 1, Pin 8 (or CN3-3)",
  "gnd_summary": "GND: Pin 4, Pin 5 (or CN2-2, CN2-4)",
  "notes": "VCC on Pin 1/8 (+5V), GND on Pin 4/5 (0V)"
}}

If pin numbers are alphanumeric (e.g. BGA or connector headers like CN3-3), convert pin numbers or include them as strings.
If pin numbers cannot be determined with certainty, return:
{{
  "part_number": "{part_number}",
  "vcc_pins": [],
  "gnd_pins": [],
  "vcc_summary": "Can't find",
  "gnd_summary": "Can't find",
  "notes": "Pinout specifications unavailable"
}}"""


def lookup_datasheet(part_number: str, ocr_engine: str = 'gemini', api_key: str = None) -> dict:
    """
    Scrapes and fetches component datasheets (PDF & HTML web view) from AllDatasheet / LCSC / FTDI.

    Args:
        part_number (str): IC part number (e.g., 'STM32F745VGT6', 'AS4C32M16D2A-25BCN').
        ocr_engine (str): OCR engine identifier.
        api_key (str): Gemini API key.

    Returns:
        dict: Containing datasheet metadata links, direct PDF URL, and HTML datasheet URL.
    """
    if not part_number or part_number.upper() in ["UNKNOWN", "NOT_IC", "SEARCHING..."]:
        return {
            'success': False,
            'error': 'Invalid or unknown part number provided.'
        }

    pn = part_number.strip()
    search_url = f"https://www.alldatasheet.com/view.jsp?Searchword={urllib.parse.quote(pn)}"
    pdf_url = None
    html_url = None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        r = requests.get(search_url, timeout=7, headers=headers)
        if r.status_code == 200:
            # 1. HTML version link match (e.g. /html-pdf/...)
            m_html = re.search(r'href=["\']?([^"\' >]*/html-pdf/[^"\' >]+\.html)["\']?', r.text, re.I)
            if m_html:
                h_href = m_html.group(1)
                if h_href.startswith("//"):
                    html_url = "https:" + h_href
                elif not h_href.startswith("http"):
                    html_url = "https://www.alldatasheet.com" + h_href
                else:
                    html_url = h_href

            # 2. Direct PDF Link Match
            m_pdf = re.search(r'href=["\']?(https://pdf\d*\.alldatasheet\.com/[^"\' >]+\.pdf)["\']?', r.text, re.I)
            if m_pdf:
                pdf_url = m_pdf.group(1)
            else:
                # 3. View Page Match
                m_view = re.search(r'href=["\']?([^"\' >]*/datasheet-pdf/pdf/[^"\' >]+)["\']?', r.text, re.I)
                if m_view:
                    view_href = m_view.group(1)
                    if view_href.startswith("//"):
                        view_href = "https:" + view_href
                    elif not view_href.startswith("http"):
                        view_href = "https://www.alldatasheet.com" + view_href

                    # Follow view page to resolve iframe/embed direct PDF source
                    try:
                        r_view = requests.get(view_href, timeout=6, headers=headers)
                        if r_view.status_code == 200:
                            m_iframe = re.search(r'(?:src|href)=["\']?(https://pdf\d*\.alldatasheet\.com/[^"\' >]+\.pdf)["\']?', r_view.text, re.I)
                            if m_iframe:
                                pdf_url = m_iframe.group(1)
                            else:
                                pdf_url = view_href
                    except Exception:
                        pdf_url = view_href
    except Exception as e_ds:
        print(f"[WARN] AllDatasheet lookup error for {pn}: {e_ds}")

    final_pdf = pdf_url or search_url
    final_html = html_url or search_url

    return {
        'success': True,
        'part_number': pn,
        'datasheet_url': final_pdf,
        'html_url': final_html,
        'is_direct_pdf': pdf_url is not None and pdf_url.endswith('.pdf'),
        'search_query': f"{pn} datasheet pdf pinout",
        'summary': f"Datasheet URL mined for {pn}."
    }


COMMON_IC_RULES = [
    (r'(1117|NCP1117|AMS1117|LM1117)', {
        'vcc_pins': [3],
        'gnd_pins': [1],
        'vcc_summary': 'Pin 3 (VIN: Power In)',
        'gnd_summary': 'Pin 1 (GND / 0V)',
        'notes': 'SOT-223 / TO-252: Pin 1 (GND), Pin 2/Tab (VOUT 3.3V), Pin 3 (VIN)'
    }),
    (r'(7805|78M05|78L05|LM78)', {
        'vcc_pins': [1],
        'gnd_pins': [2],
        'vcc_summary': 'Pin 1 (VIN: Power In)',
        'gnd_summary': 'Pin 2 (GND / 0V)',
        'notes': 'TO-220 / TO-252: Pin 1 (VIN), Pin 2 (GND), Pin 3 (VOUT +5V)'
    }),
    (r'(24C\d+|25Q\d+|W25Q\d+|25L\d+|AT24)', {
        'vcc_pins': [8],
        'gnd_pins': [4],
        'vcc_summary': 'Pin 8 (VCC +3.3V/5V)',
        'gnd_summary': 'Pin 4 (GND 0V)',
        'notes': 'Standard 8-pin SPI/I2C Flash Memory: Pin 4 (GND), Pin 8 (VCC)'
    }),
    (r'(LM358|NE5532|TL072|NE555|LM393)', {
        'vcc_pins': [8],
        'gnd_pins': [4],
        'vcc_summary': 'Pin 8 (VCC+)',
        'gnd_summary': 'Pin 4 (GND / VCC-)',
        'notes': 'Standard Dual OpAmp / Timer: Pin 4 (GND/V-), Pin 8 (VCC+)'
    }),
    (r'FT2232', {
        'vcc_pins': ['CN3-1 (VBUS)', 'CN3-3 (VCC +5V)'],
        'gnd_pins': ['CN2-2', 'CN2-4', 'CN2-6', 'CN3-2', 'CN3-4'],
        'vcc_summary': 'CN3-1 (VBUS 5V), CN3-3 (VCC 5V)',
        'gnd_summary': 'CN2-2, CN2-4, CN2-6, CN3-2, CN3-4 (GND 0V)',
        'notes': 'FT2232H Mini Module: CN3-1/3 (Power In 5V), CN2-2/4/6 & CN3-2/4 (GND)'
    }),
    (r'LAN9512', {
        'vcc_pins': ['VDD33', 'VDD12'],
        'gnd_pins': ['VSS', 'VSS_A', 'Die Paddle'],
        'vcc_summary': '3.3V / 1.2V Core Rails',
        'gnd_summary': 'VSS Paddle & VSS_A Analog Ground',
        'notes': 'QFN-64: Pin 65 (Exposed Die Paddle VSS), VDD33/12 Power Pins'
    }),
    (r'LAN9500', {
        'vcc_pins': ['VDD33', 'VDD12'],
        'gnd_pins': ['VSS', 'VSS_A'],
        'vcc_summary': '3.3V / 1.2V Core Rails',
        'gnd_summary': 'VSS Ground Pins',
        'notes': 'QFN-56: USB to Ethernet Controller Power Rails'
    }),
    (r'STM32F', {
        'vcc_pins': ['VDD', 'VDDA', 'VBAT'],
        'gnd_pins': ['VSS', 'VSSA'],
        'vcc_summary': 'VDD / VDDA / VBAT (3.3V)',
        'gnd_summary': 'VSS / VSSA (0V)',
        'notes': 'STM32 Microcontroller Power Pins'
    })
]


def extract_power_pins_llm(part_number: str, package: str = "SOIC-8", pin_count: int = 8, engine: str = 'gemini', api_key: str = None) -> dict:
    """
    3-Tier Pinout Intelligence Engine:
    1. Checks rule-based database for standard IC families (LDOs, Flash, OpAmps, FTDI, Ethernet).
    2. Scrapes web search snippets for unknown part numbers to give Gemini explicit context.
    3. Calls Gemini LMM with fallback endpoints.

    Args:
        part_number (str): IC part number.
        package (str): IC package type (e.g. 'LQFP-100', 'SOIC-8').
        pin_count (int): Pin count.
        engine (str): LLM engine identifier ('gemini').
        api_key (str): Gemini API key.

    Returns:
        dict: {'vcc_pins': [...], 'gnd_pins': [...], 'vcc_summary': '...', 'gnd_summary': '...', 'notes': '...'}
    """
    if not part_number or part_number.upper() in ["UNKNOWN", "NOT_IC", "SEARCHING..."]:
        return {'vcc_pins': [], 'gnd_pins': [], 'vcc_summary': "Can't find", 'gnd_summary': "Can't find", 'notes': 'Part number unknown.'}

    pn = part_number.strip()

    # Tier 1: Check Rule-Based Database
    for pattern, rule in COMMON_IC_RULES:
        if re.search(pattern, pn, re.I):
            return rule

    if not api_key:
        return {'vcc_pins': [], 'gnd_pins': [], 'vcc_summary': "Can't find", 'gnd_summary': "Can't find", 'notes': 'Gemini API key not configured.'}

    # Tier 2: Scrape Web Pinout Snippets for Context
    web_context = ""
    try:
        q = urllib.parse.quote(f"{pn} pinout VCC GND VDD VSS pin numbers")
        search_url = f"https://html.duckduckgo.com/html/?q={q}"
        r_web = requests.get(search_url, timeout=5, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        if r_web.status_code == 200:
            snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', r_web.text, re.S)
            web_context = " ".join([re.sub(r'<[^>]+>', '', s) for s in snippets])
    except Exception as e_web:
        print(f"[WARN] Web pinout scrape error for {pn}: {e_web}")

    context_prompt = f"Web Search Context Snippet:\n{web_context[:1000]}\n\n" if web_context else ""
    prompt = context_prompt + PROMPT_POWER_PINS.format(part_number=pn, package=package, pin_count=pin_count)

    # Tier 3: Call Gemini LMM Endpoints
    endpoints = [
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    ]

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for url in endpoints:
        for attempt in range(2):
            try:
                r = requests.post(url, json=payload, timeout=35)
                if r.status_code == 200:
                    res = r.json()
                    text_out = res['candidates'][0]['content']['parts'][0]['text']
                    data_parsed = sanitize_json_response(text_out)
                    if isinstance(data_parsed, dict):
                        # Ensure vcc_summary / gnd_summary are populated
                        if not data_parsed.get('vcc_summary') or data_parsed.get('vcc_summary') == 'N/A':
                            vcc_list = data_parsed.get('vcc_pins', [])
                            data_parsed['vcc_summary'] = ", ".join(map(str, vcc_list)) if vcc_list else "Can't find"
                        if not data_parsed.get('gnd_summary') or data_parsed.get('gnd_summary') == 'N/A':
                            gnd_list = data_parsed.get('gnd_pins', [])
                            data_parsed['gnd_summary'] = ", ".join(map(str, gnd_list)) if gnd_list else "Can't find"
                        return data_parsed
                elif r.status_code == 429:
                    time.sleep(2.0 ** attempt)
            except Exception as e:
                print(f"[WARN] Failed LLM power pin lookup attempt {attempt+1}: {e}")
                time.sleep(1.0)

    return {'vcc_pins': [], 'gnd_pins': [], 'vcc_summary': "Can't find", 'gnd_summary': "Can't find", 'notes': 'Pin lookup request timed out or failed.'}
