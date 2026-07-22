"""
datasheet_miner.py
Fetches component metadata from LCSC + AllDatasheet.
Extracts: category, pin_count, vcc_pins, gnd_pins from datasheet text.
"""
import re, urllib.parse, requests

def fetch_component_data(part_number: str) -> dict:
    """
    Returns:
    {
        part_number, manufacturer, description, category,
        package, pin_count, datasheet_url, buy_url,
        power_pins: { vcc: [14, 32], gnd: [1, 16, 31] }
    }
    """
    result = {
        "part_number":   part_number,
        "manufacturer":  None,
        "description":   None,
        "category":      classify_category(part_number),
        "package":       None,
        "pin_count":     None,
        "datasheet_url": None,
        "buy_url":       None,
        "power_pins":    {"vcc": [], "gnd": []},
        "source":        None,
    }

    if not part_number or part_number in ("UNKNOWN","EXTRACTION_FAILED","NOT_IC"):
        return result

    # ── jlcsearch lookup ───────────────────────────────────────────────────
    try:
        pn = urllib.parse.quote(part_number)
        url = f"https://jlcsearch.tscircuit.com/components/list.json?search={pn}&full=true"
        r = requests.get(url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        if r.status_code == 200:
            data = r.json()
            components = data.get("components", [])
            if components:
                p = components[0]
                result["manufacturer"] = p.get("subcategory") or p.get("subcategory_name")
                result["description"]  = p.get("description")
                result["package"]      = p.get("package")
                result["buy_url"]      = f"https://www.lcsc.com/search?q={urllib.parse.quote(part_number)}"
                result["source"]       = "jlcsearch (LCSC)"
                
                # Extract pin count from package string (e.g. "LQFP-48(7x7)" -> 48)
                pkg = result["package"] or ""
                m = re.search(r'-(\d{1,4})', pkg)
                if m:
                    result["pin_count"] = int(m.group(1))
                    
                # Format datasheet URL fallback using EasyDatasheet/AllDatasheet pattern
                # If LCSC code exists:
                lcsc_code = p.get("lcsc")
                if lcsc_code:
                    result["buy_url"] = f"https://www.lcsc.com/product-detail/C{lcsc_code}.html"
    except Exception as e:
        print(f"[WARN] jlcsearch lookup failed for {part_number}: {e}")

    # ── AllDatasheet fallback for datasheet URL ─────────────────────────
    try:
        url = (f"https://www.alldatasheet.com/view.jsp"
               f"?Searchword={urllib.parse.quote(part_number)}")
        r = requests.get(url, timeout=6,
                         headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
        if r.status_code == 200:
            m = re.search(
                r'href=["\']?(https://pdf\d*\.alldatasheet\.com/[^"\' >]+.pdf)["\']?',
                r.text, re.I)
            if m:
                result["datasheet_url"] = m.group(1)
                result["source"] = result["source"] or "AllDatasheet"
            else:
                m_href = re.search(r'href=["\']?([^"\' >]*/datasheet-pdf/pdf/[^"\' >]+)["\']?', r.text, re.I)
                if m_href:
                    url_found = m_href.group(1)
                    if url_found.startswith("//"):
                        url_found = "https:" + url_found
                    elif not url_found.startswith("http"):
                        url_found = "https://www.alldatasheet.com" + url_found
                    result["datasheet_url"] = url_found
                    result["source"] = result["source"] or "AllDatasheet"
    except Exception as e_ds:
        print(f"[WARN] AllDatasheet lookup failed: {e_ds}")

    # ── Power pin extraction via Gemini ──────────────────────────────
    if result["part_number"] not in ("UNKNOWN", "EXTRACTION_FAILED", "NOT_IC"):
        result["power_pins"] = extract_power_pins_gemini(
            result["part_number"],
            result["package"],
            result["pin_count"]
        )

    return result


def extract_power_pins_gemini(part_number, package, pin_count):
    """
    Ask Gemini to return VCC and GND pin numbers
    from its training knowledge of the part.
    No PDF parsing needed — Gemini knows major ICs.
    """
    import os, json, requests

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"vcc": [], "gnd": []}

    prompt = f"""You are an electronics datasheet expert.
For the IC part number: {part_number}
Package: {package or 'unknown'}
Pin count: {pin_count or 'unknown'}

List the pin NUMBERS (integers) for:
1. All VCC / VDD / VDDIO / power supply pins
2. All GND / VSS / ground pins

Return ONLY this JSON, nothing else:
{{
  "vcc_pins": [14, 32],
  "gnd_pins": [1, 16, 31],
  "pin_1_location": "bottom-left",
  "pin_order": "clockwise"
}}

If you don't know this part, return empty arrays."""

    url = (f"https://generativelanguage.googleapis.com/v1beta"
           f"/models/gemini-flash-latest:generateContent?key={api_key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "vcc_pins":       {"type": "ARRAY",
                                       "items": {"type": "NUMBER"}},
                    "gnd_pins":       {"type": "ARRAY",
                                       "items": {"type": "NUMBER"}},
                    "pin_1_location": {"type": "STRING"},
                    "pin_order":      {"type": "STRING"}
                }
            }
        }
    }
    import time
    max_retries = 3
    backoff = 2.0
    for attempt in range(max_retries):
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            elif r.status_code in (429, 503):
                print(f"[WARN] Gemini power pins code {r.status_code} (Attempt {attempt+1}/{max_retries}). Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                print(f"[ERROR] Gemini power pins request failed with code {r.status_code}: {r.text}")
                break
        except Exception as e:
            print(f"[WARN] Gemini power pins exception: {str(e)}. Retrying in {backoff}s...")
            time.sleep(backoff)
            backoff *= 2
            
    return {"vcc_pins": [], "gnd_pins": []}


def classify_category(pn: str) -> str:
    pn = pn.upper()
    rules = [
        (r'^STM32|^PIC\d|^ATMEGA|^ATTINY|^ESP\d|^LPC\d',
         "Programmable IC / MCU"),
        (r'^W25|^GD25|^MX25|^AT25', "Flash Memory"),
        (r'^FT\d{3}|^CH\d{3}|^CP21', "USB Bridge"),
        (r'^BCM\d|^RTL\d', "Network IC"),
        (r'^NRF|^CC\d{4}|^SI\d{4}', "RF / Wireless IC"),
        (r'^XC\d|^EP\d[A-Z]', "FPGA"),
        (r'^LM\d|^LD\d|^TPS\d|^MAX\d{4}', "Power Management IC"),
        (r'^SN74|^CD74|^74[A-Z]{2}', "Logic IC"),
        (r'^MPU\d|^LSM\d|^ICM\d', "Sensor / IMU"),
    ]
    import re
    for pattern, category in rules:
        if re.match(pattern, pn):
            return category
    return "Integrated Circuit (IC)"
