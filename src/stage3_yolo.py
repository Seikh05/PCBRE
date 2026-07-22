"""
Stage 3: YOLOv8m-OBB Oriented Component & Pin Detection Module
================================================================
This module executes deep learning inference using Oriented Bounding Box (OBB) YOLO
architectures (YOLOv8m-OBB) to detect, classify, and isolate components and pins on
surface-mount printed circuit boards (PCBs).

Mathematical & Geometric Formulation:
-------------------------------------
1. Horizontal Bounding Box (HBB) vs. Oriented Bounding Box (OBB):
   Standard object detectors output 4-parameter horizontal bounding boxes b_HBB = {x1, y1, x2, y2}.
   When components are mounted at arbitrary angles (e.g. 30°, 45°), HBB boxes overlap heavily,
   merging neighboring pads and causing severe multi-pin localization failure.

2. OBB 5-Parameter Formulation:
   OBB introduces a rotation angle parameter theta:
       b_OBB = {x_c, y_c, w, h, theta}
   Or equivalently represented as 8 polygon boundary vertices:
       P = [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
   This provides rotation-invariant component localization and isolates closely packed
   0402/0603 passive components without merging neighboring copper pads.

3. Resolution Expansion (1024x1024):
   Sub-millimeter passive elements (resistors/capacitors) lose spatial features at standard 640x640
   resolutions due to deep convolutional downsampling. Training at 1024x1024 resolution expands
   mean Average Precision (mAP@0.5) from 0.445 (YOLOv8n) to 0.749 (YOLOv8m-OBB).
"""

import os
import glob
import cv2
import numpy as np

# PyTorch 2.6+ Compatibility Patch
try:
    import torch
    original_torch_load = torch.load
    def patched_torch_load(*args, **kwargs):
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return original_torch_load(*args, **kwargs)
    torch.load = patched_torch_load
    print("[INFO] Applied PyTorch torch.load compatibility patch.")
except Exception as e_torch:
    print(f"[WARN] Torch load patch skipped: {e_torch}")

# Import Ultralytics YOLO
YOLO_AVAILABLE = False
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("[INFO] Ultralytics YOLO core initialized successfully.")
except ImportError:
    print("[WARN] Ultralytics package not found. YOLO inference disabled.")

# Model Cache Dictionary: { model_filename: YOLO_instance }
YOLO_MODELS_CACHE = {}


def list_available_models(models_dir: str = "models") -> list:
    """
    Scans the workspace root and models/ directory for available PyTorch (.pt) weights files.

    Args:
        models_dir (str): Relative or absolute path to models directory.

    Returns:
        list: Metadata dictionary list for UI model selectors.
    """
    if not YOLO_AVAILABLE:
        return []

    pt_files = glob.glob("*.pt") + glob.glob(os.path.join(models_dir, "*.pt")) + glob.glob(os.path.join(models_dir, "**/*.pt"), recursive=True)

    unique_models = {}
    for f in pt_files:
        name = os.path.basename(f)
        if name not in unique_models or "models" in f:
            unique_models[name] = f

    if "yolov8n.pt" not in unique_models:
        unique_models["yolov8n.pt"] = "yolov8n.pt"

    models_metadata = []
    for name, path in unique_models.items():
        size_mb = 0.0
        label = name
        recommended = False
        name_lower = name.lower()

        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            if "model_yolov8m" in name_lower:
                label = f"⭐ {name} (YOLOv8m-OBB Components - Recommended 50.8MB)"
                recommended = True
            elif "model_yolov8s" in name_lower:
                label = f"⚡ {name} (YOLOv8s-OBB Components - 22.2MB)"
            elif "model_yolov8n" in name_lower:
                label = f"🚀 {name} (YOLOv8n-OBB Components - 6.2MB)"
            elif "ic_pin" in name_lower:
                label = f"📍 {name} (IC Pin OBB Detector - PROBoter 6.3MB)"
            elif "port" in name_lower:
                label = f"🔌 {name} (Interface Port Detector - Roboflow 6.4MB)"
            elif "srfpcb" in name_lower or "yolov5" in name_lower:
                label = f"📜 {name} (Legacy YOLOv5x - 311MB)"
            else:
                label = f"📦 {name} ({size_mb:.1f}MB)"
        else:
            if name == "yolov8n.pt":
                label = "yolov8n.pt (Default YOLOv8n)"

        models_metadata.append({
            "filename": name,
            "label": label,
            "size_mb": size_mb,
            "recommended": recommended
        })

    # Sort recommended model to the top, then sort by size
    models_metadata.sort(key=lambda x: (not x["recommended"], -x["size_mb"]))
    return models_metadata


def load_yolo_model(model_name: str, models_dir: str = "models"):
    """
    Loads and caches a YOLO model instance by filename.

    Args:
        model_name (str): Weights filename (e.g. 'model_yolov8m.pt').
        models_dir (str): Directory containing weights.

    Returns:
        YOLO: Ultralytics YOLO model object.
    """
    if not YOLO_AVAILABLE:
        raise RuntimeError("Ultralytics package is not installed.")

    if model_name in YOLO_MODELS_CACHE:
        return YOLO_MODELS_CACHE[model_name]

    model_path = model_name if os.path.exists(model_name) else os.path.join(models_dir, model_name)
    if not os.path.exists(model_path):
        # Fallback to downloading stock weights if not local
        model_path = model_name

    print(f"[INFO] Loading YOLO model from {model_path}...")
    model = YOLO(model_path)
    YOLO_MODELS_CACHE[model_name] = model
    return model


def run_pin_detection_on_crop(crop_bgr: np.ndarray, pin_model_path: str = "models/ic_pin_yolo.pt", conf: float = 0.20) -> dict:
    """
    Runs IC pin detection on a single cropped IC package image using the IC Pin OBB model.

    Args:
        crop_bgr (np.ndarray): Cropped IC BGR image matrix.
        pin_model_path (str): Path to IC pin OBB model weights.
        conf (float): Detection confidence threshold.

    Returns:
        dict: Containing 'pin_count', 'confidence', and list of 'obb_boxes'.
    """
    if not YOLO_AVAILABLE or not os.path.exists(pin_model_path):
        return {'pin_count': 0, 'confidence': 0.0, 'obb_boxes': []}

    try:
        model = load_yolo_model(pin_model_path)
        results = model(crop_bgr, conf=conf, imgsz=640, verbose=False)
        res = results[0]

        obb_boxes = []
        if hasattr(res, 'obb') and res.obb is not None:
            h_crop, w_crop = crop_bgr.shape[:2]
            try:
                xyxyxyxy = res.obb.xyxyxyxy.cpu().numpy()
                for pts in xyxyxyxy:
                    norm_pts = []
                    for pt in pts:
                        norm_pts.append(float(pt[0]) / float(w_crop))
                        norm_pts.append(float(pt[1]) / float(h_crop))
                    obb_boxes.append(norm_pts)
            except Exception as e_obb:
                print(f"[WARN] Failed to format OBB pin coordinates: {e_obb}")

        pin_count = len(res.obb) if (hasattr(res, 'obb') and res.obb is not None) else (len(res.boxes) if hasattr(res, 'boxes') else 0)
        mean_conf = float(np.mean(res.boxes.conf.cpu().numpy())) if (hasattr(res, 'boxes') and res.boxes is not None and len(res.boxes) > 0) else 0.80

        return {
            'pin_count': pin_count,
            'confidence': round(mean_conf, 2),
            'obb_boxes': obb_boxes
        }
    except Exception as e:
        print(f"[WARN] Pin detection on crop failed: {e}")
        return {'pin_count': 0, 'confidence': 0.0, 'obb_boxes': []}
