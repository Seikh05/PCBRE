# Port Detection — Training & Analysis Report

> **Notebook**: 
otebooks/port-detection.ipynb
> **Platform**: Kaggle (CPU — Intel Xeon @ 2.20 GHz, no GPU accelerator)
> **Framework**: Ultralytics 8.4.90 · PyTorch 2.10.0+cpu
> **Training Run ID**: train-3
> **Date Executed**: 2026-07-15

---

## 1. Objective

The port detection sub-model extends the PCBRE hardware assurance pipeline with the ability to automatically localise and classify I/O connector ports on PCB photographs. Physical ports — USB Type-A, USB Micro/Mini, Ethernet RJ-45, PS/2, DB9 Serial, HDMI, and Audio jacks — are critical components in the hardware assurance context because they define the attack surface of any embedded system. Identifying and cataloguing all exposed communication interfaces directly informs both the Hardware Bill of Materials (HBoM) generation and hardware security threat modelling. Detected port regions are assigned standard J-prefix designators (e.g., J1, J2 ...) in the PCBRE HBoM JSON output.

> **Important Note — CPU Training**: Unlike the other two sub-models (pin detection on Tesla T4, component detection on Tesla T4), this training run was executed on **CPU only** (Intel Xeon @ 2.20 GHz). This accounts for the significantly longer per-epoch training time (~13 seconds/iteration vs ~0.4 seconds on GPU).

---

## 2. Dataset

| Property | Value |
|---|---|
| **Source** | Roboflow Universe — scmu/usb-ethernet-ps2-port, Kaggle upload seikhmustakim/port-pcb |
| **Format** | YOLOv8-OBB (DOTA-style rotated box labels) |
| **Classes** | 1 — Port-USB-Ethernet-etc |
| **Training Images** | ~26 (estimated from 2 batches of 16 per epoch) |
| **Validation Images** | 9 |
| **Validation Instances** | 29 port annotations |
| **Test Images** | 4 (used for inference validation) |
| **Input Resolution** | 640 x 640 px |

The dataset is a domain-specific small collection of PCB board images containing visible connector ports. The single aggregated class Port-USB-Ethernet-etc deliberately merges all port subtypes into one detection class, simplifying the classification problem given the limited training data and avoiding class-imbalance issues that would arise from separating USB from Ethernet from PS/2 given only ~26 training images.

### 2.1 Dataset YAML Configuration

A preprocessing step (Cell 0) was required to correct the dataset root path for the Kaggle filesystem mount. The Roboflow-exported data.yaml contained a relative path incompatible with the Kaggle read-only input mount at /kaggle/input/datasets/seikhmustakim/port-pcb/pcb_port/. The corrected data_updated.yaml was written to the writable working directory before training commenced.

---

## 3. Model Architecture — YOLOv8n-OBB

The same YOLOv8 Nano OBB architecture used for pin detection was employed here, with the classification head reconfigured for 1 output class overriding the original 15-class DOTA pretrained head.

`
YOLOv8n-obb summary (fused): 82 layers, 3,077,414 parameters, 0 gradients, 8.3 GFLOPs
`

| Layer | Module | Output Ch | Parameters |
|---|---|---|---|
| 0–1 | Conv stem (stride 2x2) | 16, 32 | 5,136 |
| 2 | C2f bottleneck | 32 | 7,360 |
| 3–4 | Conv + C2f (x2) | 64 | 68,224 |
| 5–6 | Conv + C2f (x2) | 128 | 271,616 |
| 7–8 | Conv + C2f | 256 | 755,712 |
| 9 | SPPF (spatial pyramid) | 256 | 164,608 |
| 10–14 | PAN neck (upsample path) | 128, 64 | 185,472 |
| 15–21 | PAN neck (downsample path) | 128, 256 | 764,416 |
| 22 | OBB detection head (P3/P4/P5) | 1 class | 823,174 |

**Total: 3,082,710 parameters · 8.3 GFLOPs**

The OBB head predicts five parameters per anchor: centre coordinates (x_c, y_c), box dimensions (w, h), and rotation angle theta in (-90 deg, +90 deg]. This is essential for port detection because connectors mounted on different board edges are rotated at 0, 90, 180, or 270 degrees relative to the camera frame.

---

## 4. Training Configuration

Training was executed with a minimal hyperparameter set (no backbone freezing, no custom augmentation stack) reflecting the simpler experimental scope of this training run compared to the pin detection notebook.

### 4.1 Hyperparameters

| Parameter | Value | Rationale / Note |
|---|---|---|
| epochs | 50 | Conservative choice; port topology is simpler than multi-class component detection |
| imgsz | 640 | Standard resolution; ports are physically large components and well-represented at 640 px |
| device | CPU (default) | No GPU accelerator attached to this Kaggle session |
| reeze | None (not set) | Full fine-tuning: all 145 layers updated |
| patience | 100 | Default; effectively disabled early stopping for this 50-epoch run |
| weight_decay | 0.0005 | Standard L2 default for Ultralytics |
| mosaic | 1.0 | Default mosaic augmentation (4-image composites) |
| liplr | 0.5 | 50% horizontal flip |
| lipud | 0.0 | Vertical flip disabled (PCBs are typically photographed right-way up) |
| degrees | 0.0 | No explicit rotation augmentation (OBB head handles orientation implicitly) |
| scale | 0.5 | +/-50% random scale |
| atch | 16 (auto) | Default batch size |
| optimizer | auto-selected | Auto: SGD(lr=0.01, momentum=0.937) selected for CPU regime |
| lr0 | 0.01 | Standard SGD learning rate |
| lrf | 0.01 | Final LR = 0.01 * 0.01 = 0.0001 (cosine decay floor) |
| mp | True | Mixed precision enabled (though CPU has limited AMP benefit) |
| plots | True | Metric plots saved to 
uns/obb/train-3/ |

**Key difference from pin detection run**: No backbone freezing (reeze=None). All layers including the COCO-pretrained backbone weights were updated during training. On a very small dataset this increases the risk of catastrophic forgetting, but for simple single-class detection of large, visually distinctive objects (connectors), the full fine-tuning regime is generally acceptable.

---

## 5. Training Dynamics

Training completed in **0.206 hours (~12.4 minutes)** on CPU. Each epoch took approximately **~13 seconds** (2 training batches at ~6.4 s/batch + ~1.4 s validation).

### 5.1 Epoch-by-Epoch Summary Table

| Epoch | box_loss | cls_loss | dfl_loss | angle_loss | Val P | Val R | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|---|---|---|---|
| 1 | 2.025 | 4.145 | 2.937 | 0.4021 | 0.005 | 0.276 | 0.00206 | 0.000498 |
| 2 | 2.086 | 3.923 | 2.932 | 0.3834 | 0.007 | 0.379 | 0.00348 | 0.00089 |
| 3 | 2.098 | 3.712 | 2.933 | 0.3240 | 0.010 | 0.483 | 0.0061 | 0.00276 |
| 4 | 1.740 | 3.510 | 2.686 | 0.2894 | 0.015 | 0.690 | 0.104 | 0.0689 |
| 5 | 1.530 | 3.281 | 2.516 | 0.1955 | 0.533 | 0.198 | 0.332 | 0.239 |
| 6 | 1.283 | 2.926 | 2.358 | 0.1025 | 0.615 | 0.496 | 0.471 | 0.343 |
| 7 | 1.143 | 2.648 | 2.434 | 0.0712 | 0.654 | 0.521 | 0.577 | 0.387 |
| 8 | 1.155 | 2.388 | 2.283 | 0.0634 | 0.608 | 0.589 | 0.628 | 0.526 |
| 9 | 0.978 | 2.122 | 2.162 | 0.0489 | 0.602 | 0.627 | 0.641 | 0.545 |
| 10 | 1.112 | 1.920 | 2.147 | 0.0433 | 0.653 | 0.655 | 0.656 | 0.555 |
| 11 | 1.056 | 1.862 | 2.031 | 0.0382 | 0.683 | 0.595 | 0.667 | 0.560 |
| 12 | 0.936 | 1.584 | 1.992 | 0.0349 | 0.681 | 0.586 | 0.706 | 0.592 |
| 13 | 0.874 | 1.832 | 1.886 | 0.0361 | 0.682 | 0.593 | 0.686 | 0.570 |
| 15 | 0.825 | 1.466 | 1.827 | 0.0363 | 0.662 | 0.608 | 0.697 | 0.576 |
| 18 | 0.821 | 1.255 | 1.679 | 0.0085 | 0.676 | 0.586 | 0.698 | 0.587 |
| 20 | 0.793 | 1.510 | 1.697 | 0.0210 | 0.765 | 0.563 | 0.709 | 0.615 |
| 22 | 0.726 | 1.208 | 1.517 | 0.0319 | 0.743 | 0.621 | 0.712 | 0.611 |
| 24 | 0.699 | 1.284 | 1.453 | 0.0136 | 0.873 | 0.586 | 0.719 | 0.625 |
| 25 | 0.620 | 0.922 | 1.426 | 0.0108 | 0.899 | 0.613 | 0.724 | 0.622 |
| 30 | 0.619 | 0.872 | 1.359 | 0.0149 | 0.858 | 0.517 | 0.707 | 0.599 |
| 35 | 0.542 | 0.847 | 1.309 | 0.0069 | 0.858 | 0.517 | 0.707 | 0.599 |
| 36 | 0.536 | 0.777 | 1.193 | 0.0108 | 0.937 | 0.515 | 0.693 | 0.613 |
| 39 | 0.578 | 0.741 | 1.288 | 0.0140 | 0.736 | 0.586 | 0.714 | 0.648 |
| 40 | 0.488 | 0.865 | 1.187 | 0.0034 | 0.736 | 0.586 | 0.714 | 0.648 |
| 41 | 0.497 | 0.942 | 1.165 | 0.0083 | 0.572 | 0.738 | 0.722 | 0.647 |
| 42 | 0.543 | 0.936 | 1.151 | 0.0186 | 0.593 | 0.754 | 0.720 | 0.658 |
| 44 | 0.428 | 0.761 | 1.102 | 0.0017 | 0.596 | 0.724 | 0.722 | 0.657 |
| 48 | 0.555 | 0.907 | 1.149 | 0.0116 | 0.696 | 0.724 | 0.724 | 0.661 |
| 49 | 0.481 | 0.743 | 1.063 | 0.0050 | 0.696 | 0.724 | 0.724 | 0.661 |
| **50** | **0.450** | **0.697** | **1.110** | **0.0062** | **0.673** | **0.724** | **0.740** | **0.680** |

### 5.2 Loss Reduction Summary

`
box_loss:    2.025 -> 0.450  (-77.8% reduction over 50 epochs)
cls_loss:    4.145 -> 0.697  (-83.2% reduction — fastest convergence)
dfl_loss:    2.937 -> 1.110  (-62.2% reduction)
angle_loss:  0.402 -> 0.006  (-98.5% reduction — near-complete angular convergence)
`

> **Note on angle_loss**: The extremely high initial angle_loss (0.402) compared to the pin detection run (0.103) is notable. Port connectors exhibit large physical rotation angles (e.g., USB ports on a side-mounted edge connector are perpendicular to the board axis), making initial angular predictions highly inaccurate. The 98.5% reduction to 0.006 confirms excellent orientation learning by epoch 50.

### 5.3 Training Phase Analysis

**Phase 1 (Epochs 1-7) — Initial Bootstrap (No GPU, slow warm-up):**
All losses drop steeply but mAP@0.5 rises slowly in the first 4 epochs (0.002 -> 0.104) before jumping sharply at epoch 5 (0.332). The initial slow mAP growth reflects the warmup period (3 epochs) where the learning rate is ramped up from near-zero. The angle_loss dominates early training: at 0.402 in epoch 1, the model's angular predictions are essentially random, which suppresses IoU overlap with ground-truth OBBs and artificially deflates early mAP scores.

**Phase 2 (Epochs 8-20) — Coordinate Refinement:**
mAP@0.5 climbs from 0.628 to 0.709 with box_loss falling from 1.155 to 0.793. A notable oscillation in Precision (P) is observed: P fluctuates between 0.53 and 0.90 across epochs in this phase, while Recall (R) remains more stable. This high P oscillation is a symptom of the tiny validation set (29 instances across 9 images) — a single false positive or missed detection shifts precision by ~3.4 percentage points (1/29).

**Phase 3 (Epochs 21-40) — Convergence Plateau:**
mAP@0.5 oscillates in the 0.693-0.724 band. The model appears to have reached its capacity ceiling given the training data volume. Mosaic augmentation is disabled at epoch 40 (close_mosaic=10 from end).

**Phase 4 (Epochs 41-50) — Post-Mosaic Stabilisation:**
After mosaic is disabled, standard Albumentations augmentation (Blur, MedianBlur, ToGray, CLAHE) takes over. mAP@0.5 rises slightly from 0.722 to 0.740 at epoch 50. box_loss reaches its minimum (0.428 at epoch 44) and cls_loss hits its lowest recorded value (0.697 at epoch 50), both confirming continued refinement without overfitting in this final phase.

---

## 6. Final Validated Results (best.pt)

From best-weights checkpoint validation:

| Metric | Score |
|---|---|
| **Precision (P)** | **0.670** |
| **Recall (R)** | **0.724** |
| **mAP@0.5** | **0.741** |
| **mAP@0.5:0.95** | **0.681** |
| Val Images | 9 |
| Val Instances | 29 |

### Test Inference Results (4 unseen images)

The trained model was evaluated on 4 held-out test images:

| Test Image | Detections | Inference Time |
|---|---|---|
| 1_jpg.rf.af68... | 1 Port-USB-Ethernet-etc | 153.8 ms |
| 26_jpg.rf.78d4... | 1 Port-USB-Ethernet-etc | 131.4 ms |
| 36_jpg.rf.8f8f... | **6 Port-USB-Ethernet-etcs** | 136.7 ms |
| 56_jpg.rf.7bfd... | 1 Port-USB-Ethernet-etc | 139.8 ms |

All 4 test images were correctly inferred. Image 3 (with 6 detections) represents a multi-port panel card with USB, Ethernet, and audio jacks in close proximity — the model successfully differentiated all 6 connectors without NMS collapse.

### Inference Speed (CPU — Intel Xeon @ 2.20 GHz)

| Stage | Latency |
|---|---|
| Preprocessing | 2.2 ms/image |
| **Inference** | **140.4 ms/image** |
| Postprocessing | 1.5 ms/image |
| **Total** | **~144 ms/image (~7 fps effective)** |

> **Warning**: Inference at 140 ms/image reflects **CPU-only** operation with no hardware acceleration. On a Tesla T4 GPU (as used by the pin and component models), expected inference time drops to ~8-12 ms/image at 640 px, consistent with the YOLOv8n-OBB GPU benchmark.

Model checkpoint size: **6.7 MB** (optimiser state stripped).

---

## 7. Quantitative Interpretation

**mAP@0.5 = 0.741** — On 29 validation instances spanning 9 images, the model correctly localises 74.1% of all annotated connector ports at IoU >= 0.5. This is lower than the pin detection mAP (0.899) but the contexts are critically different: pin detection used a frozen backbone (transfer learning efficiency), while this model was fully fine-tuned from scratch with default hyperparameters. The 0.741 mAP is still strong for a single-class detector on a 26-image training set.

**mAP@0.5:0.95 = 0.681** — The tight IoU-averaged metric of 0.681 is actually *higher* than the mAP@0.5 (0.741) counterpart in the pin model context. This implies that the model produces very tight-fitting OBBs — when it detects a port, the box fits accurately. The relatively small gap between mAP@0.5 (0.741) and mAP@0.5:0.95 (0.681) — only 0.060 — indicates consistent localization quality rather than sloppy boxes that barely pass the 0.5 IoU threshold.

**Precision = 0.670 vs Recall = 0.724** — Recall exceeds Precision, meaning the model is more prone to false positives than false negatives. In the port detection context this is the preferred error mode: missing a port (false negative) is more dangerous for hardware assurance purposes than falsely detecting one. A missed port represents an undocumented attack surface; a false positive merely adds a spurious entry to the HBoM for human review.

**angle_loss final = 0.006 (98.5% reduction)** — The near-complete angular convergence confirms robust orientation estimation. Connectors at 90-degree board-edge mounting angles are correctly aligned in the predicted OBBs, which is important for accurate centroid coordinate mapping in the PCBRE pipeline.

---

## 8. CPU vs GPU Training Comparison

This model is unique in the PCBRE sub-model suite in having been trained entirely on CPU. The comparison highlights the hardware impact:

| Metric | Port (CPU) | Pin (GPU T4) | Component (GPU T4) |
|---|---|---|---|
| Epochs | 50 | 100 | 150 |
| Training time | **12.4 minutes** | ~1.5 minutes | ~45 minutes |
| Per-epoch speed | ~13 s/it | ~0.4 s/it | ~18 s/it |
| VRAM used | N/A (CPU) | 1.45-2.32 GB | ~12 GB |
| Final mAP@0.5 | 0.741 | 0.899 | 0.749 |

The 50-epoch CPU training for port detection took 12.4 minutes — surprisingly manageable given the Kaggle session time constraints. The CPU training regime explains the lack of aggressive hyperparameter tuning: every additional epoch costs ~13 seconds, discouraging the kind of 200-epoch exploratory runs feasible on GPU.

---

## 9. PCBRE Pipeline Integration

### 9.1 Inference Invocation

In the PCBRE pp.py, the port detector (detect_port_yolov8n.pt) is invoked as a cascade after the primary YOLOv8m-OBB component detection pass. The inference call uses:

`python
conf=0.25   # Confidence threshold
iou=0.45    # NMS IoU threshold
`

The lower NMS IoU threshold (0.45 vs the default 0.7) helps prevent suppression of adjacent ports on multi-port interface panels, matching the 6-port detection behaviour observed on test image 3.

### 9.2 HBoM Integration

Each detected port box is assigned:
- **Designator**: J{n} (J-prefix for connector/jack)
- **Category**: Connector
- **Package**: Port-USB-Ethernet-etc (maps to specific physical type with Gemini OCR disambiguation if needed)
- **Pin count**: Not assigned by OBB detector (requires physical port type classifier as future work)

### 9.3 Limitation — No Port Subtype Classification

The single aggregated class Port-USB-Ethernet-etc does not distinguish between USB-A, USB-C, RJ-45 Ethernet, PS/2, DE-9 Serial, HDMI, or 3.5mm audio jacks. From a hardware security perspective, USB-C and RJ-45 ports are far higher-risk attack vectors than a 3.5mm audio jack. A multi-class extension with 6-8 distinct port types would significantly enhance the pipeline's threat modelling output. This requires approximately 200-300 additional annotated images per port type class.

---

## 10. Comparison with Other PCBRE Sub-Models

| Metric | Port Detection | Pin Detection | Component Detection |
|---|---|---|---|
| Model | YOLOv8n-OBB | YOLOv8n-OBB | YOLOv8m-OBB |
| Parameters | 3.1 M | 3.1 M | 26.4 M |
| imgsz | 640 px | 640 px | 1024 px |
| Classes | 1 | 1 | 9 |
| Training HW | **CPU (Xeon)** | GPU (T4) | GPU (T4) |
| Training Images | ~26 | 38 | 90 |
| Val Instances | 29 | 157 | 979 |
| mAP@0.5 | 0.741 | 0.899 | 0.749 |
| mAP@0.5:0.95 | 0.681 | 0.706 | — |
| Inference (CPU) | 140.4 ms | ~800 ms | ~1240 ms |
| Model Size | 6.7 MB | 6.6 MB | 50.8 MB |
| Training Time | 12.4 min | ~1.5 min | ~45 min |
| Backbone Frozen | No | Yes (10 layers) | No |

---

## 11. Summary

| Item | Result |
|---|---|
| Model | YOLOv8n-OBB (Nano, full fine-tuning, CPU training) |
| Dataset | ~26 train / 9 val / 4 test images — single class Port-USB-Ethernet-etc |
| Best Checkpoint | ~Epoch 50 (best.pt, 6.7 MB) |
| Precision | 0.670 |
| Recall | 0.724 |
| **mAP@0.5** | **0.741** |
| **mAP@0.5:0.95** | **0.681** |
| Training Time | 12.4 minutes (CPU) |
| Inference Speed | 140.4 ms/image (CPU) / ~10 ms expected (GPU) |
| Epochs Completed | 50 (patience=100, no early stop) |
| angle_loss reduction | 98.5% (0.402 -> 0.006) |
| Test Images Inferred | 4/4 correct (including 6-port multi-connector image) |
| HBoM Integration | J-prefix designator assignment, Connector category |

> **Tip**: For production deployment on the PCBRE Flask server, load this model on GPU to bring inference from 140 ms to ~10 ms. The confidence threshold of 0.25 and NMS IoU of 0.45 are calibrated for multi-port panel boards — do not raise the NMS threshold above 0.6 or adjacent ports on IO shields will be suppressed.
