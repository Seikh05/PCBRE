"""
power_overlay.py
Calculates coordinate mappings along bounding box perimeters and overlays power rail indicators.
"""
import cv2

def calculate_pin_pixel_coords(bbox, pin_count, package_type="QFP"):
    """
    Given IC bounding box + pin count, calculate
    pixel coordinates of each pin on the PCB image.

    Assumes QFP (pins on all 4 sides) — most common for ICs.
    Pin 1 = bottom-left corner, counting clockwise.

    Returns: { pin_number: (x, y) } for all pins
    """
    x1, y1, x2, y2 = [int(round(c)) for c in bbox]
    w = x2 - x1
    h = y2 - y1

    coords = {}
    
    # Safeguard if pin count is invalid or small
    if not pin_count or pin_count < 4:
        return coords

    pins_per_side = pin_count // 4
    if pins_per_side == 0:
        pins_per_side = 1

    # Bottom side: pins 1 → pins_per_side (left to right)
    for i in range(pins_per_side):
        px = x1 + int(w * (i + 0.5) / pins_per_side)
        py = y2
        coords[i + 1] = (px, py)

    # Right side: next set (bottom to top)
    for i in range(pins_per_side):
        px = x2
        py = y2 - int(h * (i + 0.5) / pins_per_side)
        coords[pins_per_side + i + 1] = (px, py)

    # Top side: (right to left)
    for i in range(pins_per_side):
        px = x2 - int(w * (i + 0.5) / pins_per_side)
        py = y1
        coords[pins_per_side * 2 + i + 1] = (px, py)

    # Left side: (top to bottom)
    for i in range(pins_per_side):
        px = x1
        py = y1 + int(h * (i + 0.5) / pins_per_side)
        coords[pins_per_side * 3 + i + 1] = (px, py)

    return coords


def plot_power_anchors(img, bbox, vcc_pins, gnd_pins, pin_count):
    """
    Draws VCC (red) and GND (blue) pin markers on PCB image.
    This is the visual output of the power rail research.
    """
    if not pin_count or pin_count < 4 or img is None:
        return img

    pin_coords = calculate_pin_pixel_coords(bbox, pin_count)
    annotated = img.copy()

    for pin_num, (px, py) in pin_coords.items():
        # Make pin_num float/int comparison safe
        is_vcc = False
        is_gnd = False
        
        # Cast pin arrays to integers for strict checks
        vcc_ints = [int(p) for p in vcc_pins if p is not None]
        gnd_ints = [int(p) for p in gnd_pins if p is not None]
        
        if int(pin_num) in vcc_ints:
            is_vcc = True
        elif int(pin_num) in gnd_ints:
            is_gnd = True

        if is_vcc:
            # Red filled circle = VCC (BGR: (0, 0, 255))
            cv2.circle(annotated, (px, py), 5, (0, 0, 255), -1)
            cv2.putText(annotated, "V", (px-4, py-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35,
                        (0, 0, 255), 1, cv2.LINE_AA)
        elif is_gnd:
            # Blue filled circle = GND (BGR: (255, 80, 0))
            cv2.circle(annotated, (px, py), 5, (255, 80, 0), -1)
            cv2.putText(annotated, "G", (px-4, py-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35,
                        (255, 80, 0), 1, cv2.LINE_AA)

    return annotated
