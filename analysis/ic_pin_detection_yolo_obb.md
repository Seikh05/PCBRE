# IC Pin Detection: YOLOv8-OBB Model Training & Integration
**Project**: Optical PCB Reverse Engineering (PCBRE)  
**Date**: July 15, 2026  
**Subject**: Training results for the local Oriented Bounding Box (OBB) pin detector and application integration pipeline.

---

## 📌 Executive Summary
To catalog IC packages and verify pin matches offline without cloud dependencies, we trained a custom **YOLOv8n-OBB** pin detection model (`ic_pin_yolo.pt`) on a dataset containing labeled PCB pin pads. 

The model achieved an outstanding validation score on Kaggle, with an **mAP@0.5 of 89.9%** and a **Precision of 90.0%**. This document outlines the model's metrics, its integration into the Flask backend, output formatting, and guidelines for production accuracy.

---

## 📊 Kaggle Training Metrics (100 Epochs)

* **Architecture**: YOLOv8n-OBB (Nano, 3.07M parameters)
* **Training Platform**: Kaggle GPU (Tesla T4)
* **Training Time**: ~1.5 minutes (0.025 hours) for 100 epochs
* **Model Size**: 6.6 MB (`ic_pin_yolo.pt`)

### Validation Performance
| Metric | Class | Images | Instances Labeled | Best Score |
| :--- | :---: | :---: | :---: | :---: |
| **Precision (P)** | Pin pads | 10 | 157 | **0.900 (90.0%)** |
| **Recall (R)** | Pin pads | 10 | 157 | **0.873 (87.3%)** |
| **mAP@0.5** | Pin pads | 10 | 157 | **0.899 (89.9%)** |
| **mAP@0.5:0.95** | Pin pads | 10 | 157 | **0.706 (70.6%)** |

### Speed Summary
* **Preprocess**: 0.2ms
* **Inference**: 2.0ms (highly optimized for real-time edge processing)
* **Postprocess**: 1.8ms

---

## 🛠️ Application Integration Architecture

We integrated this trained model directly into the Flask application structure:

```
PCBRE/
├── app.py                      ← /api/detect_pins & /api/generate_hbom
├── models/
│   └── ic_pin_yolo.pt          ← Model weights file (6.6MB)
└── templates/
    └── stage3_yolo.html        ← "Detect IC Pins" UI Button & Table
```

### 1. Flask API Integration (`/api/detect_pins`)
Accepts a PCB image, runs the base YOLO model to detect ICs, crops each IC, and executes the pin OBB model on each crop. It returns:
* `results`: A list containing the designator, crop coordinates, pin counts, and raw YOLO OBB coordinates.
* `annotated_image`: A base64 image featuring:
  * Bold blue IC boundary boxes (thickness 4)
  * Bright cyan oriented pin boundaries (thickness 2)

### 2. YOLO OBB Label Output Format
To assist with downstream labeling or direct model consumption, the API exports pin coordinates in standard YOLO OBB text format (`class_id x1 y1 x2 y2 x3 y3 x4 y4` normalized to $[0.0, 1.0]$):
* `yolo_obb_crop`: Coordinates normalized relative to the **crop image boundaries**.
* `yolo_obb_main`: Coordinates mapped back and normalized relative to the **original main image**.

---

## 🔍 Diagnostic: Addressing Low Crop Inference Accuracy

While the validation accuracy is **89.9% mAP**, running pin detection on small cropped chip regions locally can yield lower counts. This is caused by:

### 1. Scale Mismatch
* **Observation**: The validation set averaged ~16 pins per image, showing that the model was trained on larger views of the PCB (where pins represent a tiny fraction of the total resolution).
* **Problem**: Cropping a single IC and stretching it to the square $640\text{px}$ YOLO input enlarges the pins. The model's convolutional kernels are tuned for small features and fail to fire on these enlarged pins.

### 2. Resolution Loss
* Any downscaling of the main image during upload reduces the pixel density of the pins, causing edge-detection features to fail.

### 💡 Recommendation
For maximum accuracy, feed the **full original PCB image** directly to the `ic_pin_yolo.pt` model at a high resolution (e.g. `imgsz=1024` or `1280`), rather than cropping sub-regions first. This matches the native scale the model learned during Kaggle training.
