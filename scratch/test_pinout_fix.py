import requests
import json
import re
import urllib.parse
from src.utils import sanitize_json_response

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
    })
]

def check_rules(part_number):
    for pattern, rule in COMMON_IC_RULES:
        if re.search(pattern, part_number, re.I):
            return rule
    return None

print("NCP1117ST33G ->", check_rules("NCP1117ST33G"))
print("LAN9512-JZX ->", check_rules("LAN9512-JZX"))
print("W25Q128JV ->", check_rules("W25Q128JV"))
print("LM358DR ->", check_rules("LM358DR"))
print("FT2232H-56Q ->", check_rules("FT2232H-56Q"))
