"""
Pin Detection Inference Script
Runs ic_pin_yolo.pt on all images in the test images folder
and saves annotated results to the pin_detection model_plots folder.
"""

import sys
import os
from pathlib import Path
import cv2
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
BASE        = Path(r"c:\Users\91955\OneDrive\Desktop\PCBRE")
MODEL_PATH  = BASE / "models" / "ic_pin_yolo.pt"
SRC_DIR     = BASE / "datasets" / "yolo_pins_dataset" / "test images"
OUT_DIR     = BASE / "Internship Report assets" / "model_plots" / "pin_detection"

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
LINE_W    = 2             # OBB line width (px)

# Colour palette (BGR)
COLOURS = [(0, 200, 255), (0, 255, 120), (255, 80, 0), (200, 0, 255)]

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
    n_det   = 0

    if result.obb is not None and len(result.obb) > 0:
        obb_data = result.obb  # ultralytics OBB result object

        for idx, box in enumerate(obb_data):
            n_det += 1
            colour = COLOURS[idx % len(COLOURS)]

            # xyxyxyxy gives the 4 corner points (x1,y1, x2,y2, x3,y3, x4,y4)
            pts = box.xyxyxyxy.cpu().numpy().reshape(4, 2).astype(np.int32)
            # confidence / label not displayed

            # Draw filled-transparent polygon + border
            overlay = canvas.copy()
            cv2.fillPoly(overlay, [pts], colour)
            cv2.addWeighted(overlay, 0.20, canvas, 0.80, 0, canvas)
            cv2.polylines(canvas, [pts], isClosed=True, color=colour, thickness=LINE_W)

    # ── Save ─────────────────────────────────────────────────────────────
    stem     = img_path.stem
    out_path = OUT_DIR / f"pin_inference_{stem}.png"
    cv2.imwrite(str(out_path), canvas)

    summary_rows.append((img_path.name, w, h, n_det))
    print(f"    Detected {n_det} pins  →  saved: {out_path.name}")

# ── Print summary ─────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"{'Image':<30} {'W':>5} {'H':>5} {'Pins':>6}")
print("-" * 60)
for name, w, h, n in summary_rows:
    print(f"{name:<30} {w:>5} {h:>5} {n:>6}")
print("=" * 60)
print(f"[DONE] {len(summary_rows)} images saved to: {OUT_DIR}")
