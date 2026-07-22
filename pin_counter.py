"""
pin_counter.py
Counts visible pins on IC perimeter using Computer Vision contour heuristics.
"""
import cv2
import numpy as np

def estimate_pin_count(crop_bgr: "np.ndarray") -> dict:
    """
    Counts visible pins on IC perimeter using CV.
    Returns: { "detected_pins": int, "confidence": str, "side_counts": dict }
    
    Works by:
    1. Sobel edge detection / Adaptive Threshold on grayscale crop
    2. Isolate perimeter strip (12% border of bbox)
    3. Find contours matching pin properties (periodic bright segments)
    4. Count along each of 4 sides
    """
    if crop_bgr is None or crop_bgr.size == 0:
        return {
            "detected_pins": 0,
            "side_counts": {"top": 0, "bottom": 0, "left": 0, "right": 0},
            "confidence": "LOW"
        }

    h, w = crop_bgr.shape[:2]
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)

    # CLAHE for contrast on metallic pins
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4,4))
    enhanced = clahe.apply(gray)

    # Adaptive threshold — isolates bright metallic pins
    binary = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, -2
    )

    total_pins = 0
    side_counts = {"top": 0, "bottom": 0, "left": 0, "right": 0}
    margin = max(int(min(h, w) * 0.12), 8)

    # Analyse each perimeter strip
    # Make sure slices are within boundary coordinates
    top_strip = binary[0:margin, margin:w-margin] if h > margin and w > 2*margin else np.array([])
    bottom_strip = binary[h-margin:h, margin:w-margin] if h > margin and w > 2*margin else np.array([])
    left_strip = binary[margin:h-margin, 0:margin] if h > 2*margin and w > margin else np.array([])
    right_strip = binary[margin:h-margin, w-margin:w] if h > 2*margin and w > margin else np.array([])

    strips = {
        "top":    top_strip,
        "bottom": bottom_strip,
        "left":   left_strip,
        "right":  right_strip,
    }

    for side, strip in strips.items():
        if strip is None or strip.size == 0:
            continue
        cnts, _ = cv2.findContours(
            strip, cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        # Filter contours by aspect ratio
        # Pins are small rectangles, not blobs
        valid = []
        for c in cnts:
            x, y, cw, ch = cv2.boundingRect(c)
            area = cw * ch
            if area < 8 or area > strip.size * 0.25:
                continue
            ar = max(cw, ch) / max(min(cw, ch), 1)
            if 1.0 <= ar <= 8.0:
                valid.append(c)
        side_counts[side] = len(valid)
        total_pins += len(valid)

    # Confidence: higher if opposite sides have similar counts
    top_bot_diff = abs(side_counts["top"] - side_counts["bottom"])
    lft_rgt_diff = abs(side_counts["left"] - side_counts["right"])
    symmetry_ok  = (top_bot_diff <= 2 and lft_rgt_diff <= 2)
    confidence   = "HIGH" if symmetry_ok else "LOW"

    return {
        "detected_pins": total_pins,
        "side_counts":   side_counts,
        "confidence":    confidence,
    }
