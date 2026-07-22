import requests
import json
import re
import urllib.parse

def fetch_lcsc_pinout(part_number):
    pn = urllib.parse.quote(part_number)
    url = f"https://jlcsearch.tscircuit.com/components/list.json?search={pn}&full=true"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200:
            data = r.json()
            comps = data.get("components", [])
            if comps:
                p = comps[0]
                print(f"[LCSC] {part_number} -> Package: {p.get('package')}, Description: {p.get('description')}")
                return p
    except Exception as e:
        print(f"[ERR] LCSC: {e}")
    return None

def fetch_web_snippets(part_number):
    pn = urllib.parse.quote(f"{part_number} pinout VCC GND VDD VSS pin numbers")
    url = f"https://html.duckduckgo.com/html/?q={pn}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=7)
        if r.status_code == 200:
            snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', r.text, re.S)
            text = " ".join([re.sub(r'<[^>]+>', '', s) for s in snippets])
            print(f"[WEB] {part_number} snippet ({len(text)} chars):\n{text[:400]}\n")
            return text
    except Exception as e:
        print(f"[ERR] WEB: {e}")
    return ""

for part in ['LAN9512', 'NCP1117ST33G', 'STM32F745', 'FT2232H']:
    fetch_lcsc_pinout(part)
    fetch_web_snippets(part)
