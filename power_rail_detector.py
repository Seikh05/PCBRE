"""
power_rail_detector.py
Handles computer vision heuristics for trace width classification near coordinates,
and checks for power management components from part numbers.
"""
import cv2
import numpy as np
import re

POWER_IC_PREFIXES = [
    "LD3", "LM31", "LM78", "LM79", "TPS", "LTC", "MAX1",
    "AMS", "MCP1", "NCP", "AP1", "XC6", "HT7", "MIC5"
]

def is_power_ic(part_number: str) -> bool:
    """
    Checks if a part number corresponds to a power regulator/converter IC.
    """
    if not part_number:
        return False
    pn = part_number.upper()
    return any(pn.startswith(p.upper()) for p in POWER_IC_PREFIXES)

def classify_traces_near_label(img_bgr: np.ndarray, x_pct: float, y_pct: float) -> dict:
    """
    Calculates trace thickness at the given relative coordinates (x_pct, y_pct) on the image.
    Uses distance transform to extract trace diameter in pixels.
    """
    if img_bgr is None or img_bgr.size == 0:
        return {"max_width_px": 0.0, "is_power_trace": False}

    h, w = img_bgr.shape[:2]
    cx = int(x_pct / 100.0 * w)
    cy = int(y_pct / 100.0 * h)

    # 1. Take a 100x100 pixel local patch centered at (cx, cy)
    margin = 50
    x_min = max(0, cx - margin)
    x_max = min(w, cx + margin)
    y_min = max(0, cy - margin)
    y_max = min(h, cy + margin)

    patch = img_bgr[y_min:y_max, x_min:x_max]
    if patch.size == 0:
        return {"max_width_px": 0.0, "is_power_trace": False}

    # 2. Convert to grayscale and enhance contrast (CLAHE)
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 3. Otsu binarization to segment copper traces (assumed brighter than substrate)
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 4. Calculate Distance Transform (calculates distance from every pixel to nearest background)
    dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    max_val = float(dist.max())
    
    # 5. Trace diameter is roughly 2 * max distance transform value
    max_width_px = max_val * 2.0
    
    # Heuristic limit: traces exceeding 6.0 pixels are usually power rails/buses
    is_power = max_width_px > 6.0

    return {
        "max_width_px": round(max_width_px, 1),
        "is_power_trace": is_power
    }
