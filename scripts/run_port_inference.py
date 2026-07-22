"""
Port Detection Batch Inference Script
Runs detect_port_yolov8n.pt on all images in the proboter pcb-internal folder
and saves annotated results to the port_inference directory.
"""

import sys
import os
from pathlib import Path
import cv2
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
BASE        = Path(r"c:\Users\91955\OneDrive\Desktop\PCBRE")
MODEL_PATH  = BASE / "models" / "detect_port_yolov8n.pt"
SRC_DIR     = BASE / "datasets" / "pcb_image_proboters" / "pcb-internal"
OUT_DIR     = BASE / "yolo_results" / "ports_inference"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Load model ─────────────────────────────────────────────────────────────
print(f"[INFO] Loading model: {MODEL_PATH}")
from ultralytics import YOLO
model = YOLO(str(MODEL_PATH))

# ── Collect images ──────────────────────────────────────────────────────────
IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
images   = sorted([p for p in SRC_DIR.iterdir() if p.suffix.lower() in IMG_EXTS])

if not images:
    print(f"[ERROR] No images found in: {SRC_DIR}")
    sys.exit(1)

print(f"[INFO] Found {len(images)} images → running inference")
print(f"[INFO] Output directory: {OUT_DIR}\n")

# ── Inference & render ──────────────────────────────────────────────────────
CONF      = 0.25          # detection confidence threshold
IOU       = 0.45          # NMS IoU threshold
LINE_W    = 3             # Bounding box line width (px)

# Colour palette (BGR)
COLOURS = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255), (255, 255, 0)]

summary_rows = []

for img_path in images:
    print(f"  Processing: {img_path.name}")
    img_bgr = cv2.imread(str(img_path))
    if img_bgr is None:
        print(f"  [WARN] Could not read {img_path.name}, skipping.")
        continue

    h, w = img_bgr.shape[:2]
    canvas = img_bgr.copy()

    results = model.predict(
        source=img_bgr,
        conf=CONF,
        iou=IOU,
        verbose=False
    )

    result  = results[0]
    
    # Determine the count of detections
    n_det = 0
    if hasattr(result, 'obb') and result.obb is not None:
        n_det = len(result.obb)
    elif hasattr(result, 'boxes') and result.boxes is not None:
        n_det = len(result.boxes)

    # Use native YOLOv8 plotting which renders true rotated OBB style bounding boxes
    canvas = result.plot(line_width=LINE_W)

    # ── Save ─────────────────────────────────────────────────────────────
    stem     = img_path.stem
    out_path = OUT_DIR / f"port_inference_{stem}.png"
    cv2.imwrite(str(out_path), canvas)

    summary_rows.append((img_path.name, w, h, n_det))
    print(f"    Detected {n_det} ports  →  saved: {out_path.name}")

# ── Print summary ─────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"{'Image':<30} {'W':<5} {'H':<5} {'Ports':<6}")
print("-" * 60)
for name, w, h, n in summary_rows:
    print(f"{name:<30} {w:<5} {h:<5} {n:<6}")
print("=" * 60)
print(f"[DONE] {len(summary_rows)} images saved to: {OUT_DIR}")
