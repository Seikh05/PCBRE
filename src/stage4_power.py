"""
Stage 4: Probe-Free Power Rail Profiling & Net Mapping Module
==============================================================
This module performs optical power net (VCC / GND) identification without physical
multimeter contact probing by combining Euclidean Distance Transform (EDT) trace width
measurement, IPC-2221 conductor design heuristics, and Gemini LMM silkscreen label matching.

Mathematical & Physical Principles:
-----------------------------------
1. Euclidean Distance Transform (EDT):
   For every foreground copper trace pixel p, EDT computes the shortest Euclidean distance D(p)
   to the nearest background substrate boundary pixel B^c:
       D(p) = min_{q in B^c} ||p - q||_2

2. Trace Conductor Thickness Extraction:
   Along the trace centerline (medial axis), local conductor thickness (width) equals twice the EDT value:
       Width(p) = 2 * max_p D(p)

3. IPC-2221 Conductor Current-Carrying Design Standards:
   The IPC-2221 standard dictates that power nets (VCC/GND) carry higher current densities
   (1A to 5A) than high-speed signal lines (<10mA). Consequently, PCB layout designers construct
   power buses significantly wider. Traces exceeding a width threshold (e.g. 6.0px) are flagged
   as candidate power buses.

4. Silkscreen Label Linkage:
   Gemini 1.5 Flash scans silkscreen text near wide trace nodes (e.g. 'GND', '5V', '3V3').
   Matching text nodes propagate net identities across connected copper components, producing a
   non-destructive visual power rail map.
"""

import cv2
import numpy as np
import requests
from src.stage2_ocr import query_gemini_ocr_raw

# Prompt to extract silkscreen power labels
SILKSCREEN_POWER_PROMPT = """You are an expert PCB reverse engineering assistant.
Analyze this high-resolution PCB image and locate all silkscreen text labels indicating power, ground, or voltage rails.

Examples of power labels:
- "GND", "GROUND", "GND_PAD", "0V"
- "VCC", "VDD", "5V", "+5V", "3V3", "3.3V", "+12V", "VIN", "BAT"

For EACH label found, output:
1. "label": The exact text string printed on the board (e.g., "GND", "5V").
2. "type": "GND" if it represents ground, "VCC" if it represents a power/voltage rail.
3. "center_x": Normalized X coordinate (0.0 to 1.0) of the label text center.
4. "center_y": Normalized Y coordinate (0.0 to 1.0) of the label text center.

Return ONLY a JSON list of objects:
[
  {"label": "GND", "type": "GND", "center_x": 0.25, "center_y": 0.42},
  {"label": "5V", "type": "VCC", "center_x": 0.81, "center_y": 0.15}
]

If no power/ground silkscreen labels are visible, return an empty JSON array []."""


def compute_distance_transform_widths(binary_trace_mask: np.ndarray) -> np.ndarray:
    """
    Computes Euclidean Distance Transform (EDT) for binary trace image.

    Args:
        binary_trace_mask (np.ndarray): Binary image where copper traces = 255.

    Returns:
        np.ndarray: Trace width map matrix where each pixel value = trace width in pixels.
    """
    # cv2.distanceTransform computes radius (distance to nearest 0 pixel)
    dist = cv2.distanceTransform(binary_trace_mask, cv2.DIST_L2, 5)
    # Width = 2 * radius
    width_map = dist * 2.0
    return width_map


def query_gemini_power_labels(img_base64: str, api_key: str) -> list:
    """
    Queries Gemini Flash LMM to extract silkscreen ground & power labels with 0.0-1.0 coords.

    Args:
        img_base64 (str): Base64 data URI string of PCB image.
        api_key (str): Gemini API key.

    Returns:
        list: Extracted label dictionaries [{'label': 'GND', 'type': 'GND', 'center_x': 0.25, ...}]
    """
    if not api_key:
        return []

    if ',' in img_base64:
        encoded = img_base64.split(',', 1)[1]
    else:
        encoded = img_base64

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": SILKSCREEN_POWER_PROMPT},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded
                    }
                }
            ]
        }]
    }

    try:
        r = requests.post(url, json=payload, timeout=25)
        if r.status_code == 200:
            res = r.json()
            text_out = res['candidates'][0]['content']['parts'][0]['text']
            from src.utils import sanitize_json_response
            parsed = sanitize_json_response(text_out)
            return parsed if isinstance(parsed, list) else []
    except Exception as e:
        print(f"[WARN] Gemini power rail parsing exception: {e}")
    return []


def generate_power_rail_svg(width: int, height: int, vcc_traces: list, gnd_traces: list) -> str:
    """
    Generates an SVG overlay of power rails with glowing visual paths.

    Args:
        width (int): Image width.
        height (int): Image height.
        vcc_traces (list): Contour list for VCC traces.
        gnd_traces (list): Contour list for GND traces.

    Returns:
        str: Clean SVG string ready for Web UI overlay rendering.
    """
    svg_header = f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;">\n'
    svg_defs = """
    <defs>
      <filter id="glow-vcc" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="3" result="blur" />
        <feComposite in="SourceGraphic" in2="blur" operator="over" />
      </filter>
      <filter id="glow-gnd" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="3" result="blur" />
        <feComposite in="SourceGraphic" in2="blur" operator="over" />
      </filter>
    </defs>
    """
    svg_body = ""

    # Add VCC traces (Red)
    for cnt in vcc_traces:
        pts = " ".join([f"{p[0][0]},{p[0][1]}" for p in cnt])
        svg_body += f'  <polygon points="{pts}" fill="rgba(239, 68, 68, 0.45)" stroke="#EF4444" stroke-width="2" filter="url(#glow-vcc)" />\n'

    # Add GND traces (Blue)
    for cnt in gnd_traces:
        pts = " ".join([f"{p[0][0]},{p[0][1]}" for p in cnt])
        svg_body += f'  <polygon points="{pts}" fill="rgba(59, 130, 246, 0.45)" stroke="#3B82F6" stroke-width="2" filter="url(#glow-gnd)" />\n'

    return svg_header + svg_defs + svg_body + "</svg>"
