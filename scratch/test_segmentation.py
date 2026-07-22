import cv2
import numpy as np
import os

img_path = "static/test_images/DSC00601.JPG"
if not os.path.exists(img_path):
    # try another image
    img_path = "static/test_images/router_pcb.png"

print(f"Loading {img_path}...")
img = cv2.imread(img_path)
if img is None:
    print("Failed to load image.")
    exit(1)

h, w = img.shape[:2]
print(f"Dimensions: {w}x{h}")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Method 1: Otsu Thresholding (current implementation)
_, otsu_mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
otsu_pct = np.sum(otsu_mask == 255) / (w * h) * 100
print(f"Otsu threshold white pixel percentage: {otsu_pct:.2f}%")

# Compute distance transform for Otsu
otsu_dist = cv2.distanceTransform(otsu_mask, cv2.DIST_L2, 5)
otsu_width = otsu_dist * 2.0
otsu_max = np.max(otsu_width)
print(f"Otsu max width value: {otsu_max}")

# Method 2: Adaptive Thresholding
adaptive_mask = cv2.adaptiveThreshold(
    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 101, 3
)
adaptive_pct = np.sum(adaptive_mask == 255) / (w * h) * 100
print(f"Adaptive threshold white pixel percentage: {adaptive_pct:.2f}%")

# Compute distance transform for Adaptive
adaptive_dist = cv2.distanceTransform(adaptive_mask, cv2.DIST_L2, 5)
adaptive_width = adaptive_dist * 2.0
adaptive_max = np.max(adaptive_width)
print(f"Adaptive max width value: {adaptive_max}")

# Find contours for both
for th in [6.0, 12.0, 20.0]:
    otsu_cnts, _ = cv2.findContours(
        np.uint8(otsu_width >= th) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    adaptive_cnts, _ = cv2.findContours(
        np.uint8(adaptive_width >= th) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    print(f"Threshold={th}px:")
    print(f"  Otsu contours count: {len(otsu_cnts)}")
    print(f"  Adaptive contours count: {len(adaptive_cnts)}")
