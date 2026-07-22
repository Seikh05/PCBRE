"""
Stage 1: Classical Substrate Segmentation & Heuristic Tuning Module
====================================================================
This module implements classical computer vision heuristics (Kleber et al. baseline)
for isolating background resin substrate (green, blue, black solder masks) from
foreground IC microchips and copper traces using HSV color-space thresholding.

Mathematical & Theoretical Principle:
-------------------------------------
1. Color-Space Transformation:
   Converts standard BGR images to Hue-Saturation-Value (HSV) space. HSV decouples
   chromaticity (Hue H and Saturation S) from luminance/intensity (Value V), providing
   greater invariance to non-uniform laboratory lighting:
       H in [0, 180], S in [0, 255], V in [0, 255]

2. Binary Thresholding Mask:
   Mask M(x,y) = 1 if (H_min <= H <= H_max) and (S_min <= S <= S_max) and (V_min <= V <= V_max)
               = 0 otherwise.

3. Morphological Filtering:
   Applies Opening (erosion followed by dilation) to eliminate small noise blobs:
       A o B = (A (-) B) (+) B
   Applies Closing (dilation followed by erosion) to fill pinholes within IC bodies:
       A . B = (A (+) B) (-) B

Why Classical Substrate Segmentation Fails (Theoretical Justification):
-----------------------------------------------------------------------
- Manual Calibration Vulnerability: Different solder mask dye chemistry varies Hue by ±15 units.
  Red, black, or blue PCBs require manual slider recalibration.
- Specular Highlights: Metallic solder pads and pins reflect directional light, driving Value V to 255
  and dropping Saturation S to 0, which tricks HSV filters into misclassifying pads as IC bodies.
- Lack of Semantics: Yields unclassified binary contours. Cannot distinguish an IC package
  from a capacitor or heatsink, necessitating Stage 3 deep learning (YOLOv8-OBB).
"""

import cv2
import numpy as np


def segment_pcb_substrate(
    img: np.ndarray,
    h_lower: int = 35,
    h_upper: int = 85,
    s_lower: int = 40,
    s_upper: int = 255,
    v_lower: int = 40,
    v_upper: int = 255,
    kernel_size: int = 5,
    min_area: int = 500
) -> dict:
    """
    Executes Stage 1 HSV substrate segmentation and morphological filtering.

    Args:
        img (np.ndarray): Original OpenCV BGR image matrix.
        h_lower (int): Lower Hue bound (0-180). Default 35 (Green).
        h_upper (int): Upper Hue bound (0-180). Default 85.
        s_lower (int): Lower Saturation bound (0-255).
        s_upper (int): Upper Saturation bound (0-255).
        v_lower (int): Lower Value/Brightness bound (0-255).
        v_upper (int): Upper Value/Brightness bound (0-255).
        kernel_size (int): Structural element matrix dimensions for morphology.
        min_area (int): Minimum contour area in pixels to filter out noise.

    Returns:
        dict: Containing:
            - 'binary_mask': Binary 0/255 mask of non-substrate foreground components.
            - 'segmented_overlay': BGR image with non-substrate regions highlighted.
            - 'contours_count': Number of component contours isolated.
            - 'bounding_boxes': List of isolated candidate bounding boxes [[x, y, w, h], ...].
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Define substrate color bounds in HSV
    lower_bound = np.array([h_lower, s_lower, v_lower], dtype=np.uint8)
    upper_bound = np.array([h_upper, s_upper, v_upper], dtype=np.uint8)

    # Create binary mask (Substrate = 255, Foreground = 0)
    substrate_mask = cv2.inRange(hsv, lower_bound, upper_bound)

    # Invert mask so Foreground (components/chips) = 255
    foreground_mask = cv2.bitwise_not(substrate_mask)

    # Apply Morphological Operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    # Opening: removes small specular noise points
    cleaned_mask = cv2.morphologyEx(foreground_mask, cv2.MORPH_OPEN, kernel)
    # Closing: fills small holes inside chip packages
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)

    # Find contours of candidate components
    contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bounding_boxes = []
    annotated_overlay = img.copy()

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= min_area:
            x, y, w, h = cv2.boundingRect(cnt)
            bounding_boxes.append([x, y, w, h])
            # Draw green bounding box around classical heuristic detections
            cv2.rectangle(annotated_overlay, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return {
        'binary_mask': cleaned_mask,
        'segmented_overlay': annotated_overlay,
        'contours_count': len(bounding_boxes),
        'bounding_boxes': bounding_boxes
    }
