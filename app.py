"""
PCBRE: Flask Web Application Backend
====================================
Main application entry point for the PCBRE (Optical PCB Reverse Engineering) framework.
Imports modular pipeline stages from the `src` package and exposes RESTful API endpoints
and web views for real-time visual auditing.

Author: Seikh Souvagya Mustakim
Institution: Indian Institute of Science (IISc), DESE
"""

import os
import cv2
import numpy as np
import requests
from flask import Flask, render_template, request, jsonify

# Import Modular Stage Services from `src` Package
from src.config import (
    resolve_gemini_api_key,
    PIN_MODEL_PATH,
    DEFAULT_CONF_THRESH,
    DEFAULT_IOU_THRESH,
    DEFAULT_IMG_SZ,
    DEFAULT_POWER_TRACE_THRESH
)
from src.utils import (
    decode_base64_image,
    encode_image_base64,
    crop_and_scale_component
)
from src.stage1_segmentation import segment_pcb_substrate
from src.stage2_ocr import (
    apply_clahe,
    apply_unsharp_mask,
    query_gemini_ocr_raw,
    query_gemini_ocr_batch
)
from src.stage3_yolo import (
    list_available_models,
    load_yolo_model,
    run_pin_detection_on_crop,
    YOLO_AVAILABLE
)
from src.stage4_power import (
    compute_distance_transform_widths,
    query_gemini_power_labels,
    generate_power_rail_svg
)
from src.datasheet_miner import (
    lookup_datasheet,
    extract_power_pins_llm
)

# Initialize Flask Application
app = Flask(__name__)


# ==============================================================================
# WEB PAGE NAVIGATION ROUTES
# ==============================================================================

@app.route('/')
def index():
    """Renders the primary PCBRE Dashboard with distinct baseline & proposed modules."""
    return render_template('dashboard.html')



@app.route('/tuner/segmentation')
def stage1_tuner():
    """Renders Stage 1: Classical Substrate HSV Masking Tuner."""
    return render_template('stage1_tuner.html')

@app.route('/tuner/ocr')
def stage2_ocr():
    """Renders Stage 2: Classical OCR Preprocessing & Sharpening Tuner."""
    return render_template('stage2_ocr.html')

@app.route('/detector/yolo')
def stage3_yolo():
    """Renders Stage 3: YOLOv8m-OBB Component Detector & Gemini LMM OCR Viewer."""
    return render_template('stage3_yolo.html')

@app.route('/detector/power')
def stage4_power():
    """Renders Stage 4: Distance Transform Power Net Mapper & Visual Profiler."""
    return render_template('stage4_power.html')


# ==============================================================================
# API ROUTE: GEMINI API KEY VERIFICATION
# ==============================================================================

@app.route('/api/verify_key', methods=['POST'])
def verify_api_key():
    """
    Tests the validity of a Gemini API key.
    Checks the request payload / header first, then environment variable.
    """
    api_key = resolve_gemini_api_key(request)
    if not api_key:
        return jsonify({'valid': False, 'message': 'No API key provided.'}), 400

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "Respond with the single word: OK"}]}]}

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return jsonify({
                'valid': True,
                'message': 'Gemini API Key is valid and active!',
                'source': 'User UI Key' if request.headers.get('X-Gemini-API-Key') else 'System Default (.env)'
            })
        else:
            return jsonify({
                'valid': False,
                'message': f'API Key check failed (HTTP {r.status_code}): {r.text[:150]}'
            }), 400
    except Exception as e:
        return jsonify({'valid': False, 'message': f'Key check connection error: {str(e)}'}), 500


# ==============================================================================
# STAGE 1 API: SUBSTRATE HSV SEGMENTATION
# ==============================================================================

@app.route('/api/segment_pcb', methods=['POST'])
def api_segment_pcb():
    """
    Executes Stage 1 Substrate HSV Color Thresholding and Morphological Filtering.
    """
    data = request.get_json(silent=True) or {}
    if 'image' not in data:
        return jsonify({'success': False, 'error': 'No image provided.'}), 400

    try:
        img = decode_base64_image(data['image'])
        h_lower = int(data.get('h_lower', 35))
        h_upper = int(data.get('h_upper', 85))
        s_lower = int(data.get('s_lower', 40))
        s_upper = int(data.get('s_upper', 255))
        v_lower = int(data.get('v_lower', 40))
        v_upper = int(data.get('v_upper', 255))
        kernel_sz = int(data.get('kernel_size', 5))
        min_area  = int(data.get('min_area', 500))

        res = segment_pcb_substrate(
            img, h_lower, h_upper, s_lower, s_upper, v_lower, v_upper,
            kernel_size=kernel_sz, min_area=min_area
        )

        return jsonify({
            'success': True,
            'binary_mask': encode_image_base64(res['binary_mask'], format_ext='.png'),
            'segmented_overlay': encode_image_base64(res['segmented_overlay'], format_ext='.jpg'),
            'contours_count': res['contours_count'],
            'bounding_boxes': res['bounding_boxes']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# STAGE 2 API: OCR PREPROCESSING & GEMINI LMM OCR
# ==============================================================================

@app.route('/api/process_ocr', methods=['POST'])
def api_process_ocr():
    """
    Applies CLAHE and Gaussian Unsharp Masking to enhance IC package text.
    """
    data = request.get_json(silent=True) or {}
    if 'image' not in data:
        return jsonify({'success': False, 'error': 'No image provided.'}), 400

    try:
        img = decode_base64_image(data['image'])
        clip_limit = float(data.get('clip_limit', 3.0))
        grid_sz    = int(data.get('grid_size', 8))
        sigma      = float(data.get('sigma', 1.0))
        alpha      = float(data.get('alpha', 1.5))

        clahe_img   = apply_clahe(img, clip_limit=clip_limit, tile_grid_size=grid_sz)
        sharpened   = apply_unsharp_mask(clahe_img, sigma=sigma, alpha=alpha)

        return jsonify({
            'success': True,
            'clahe_image': encode_image_base64(clahe_img, format_ext='.jpg'),
            'sharpened_image': encode_image_base64(sharpened, format_ext='.jpg')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/run_gemini_ocr', methods=['POST'])
def api_run_gemini_ocr():
    """
    Executes single-crop OCR using Gemini 1.5 Flash LMM.
    Resolves API key dynamically from request headers/body or environment variable.
    """
    data = request.get_json(silent=True) or {}
    if 'image' not in data:
        return jsonify({'success': False, 'error': 'No image provided.'}), 400

    api_key = resolve_gemini_api_key(request)
    if not api_key:
        return jsonify({'success': False, 'error': 'Gemini API key is not configured. Add your key in the top settings bar or .env file.'}), 400

    try:
        raw_uri = data['image']
        if ',' in raw_uri:
            mime_part, encoded = raw_uri.split(',', 1)
            mime_type = mime_part.split(';')[0].split(':')[1]
        else:
            encoded = raw_uri
            mime_type = "image/jpeg"

        text_out = query_gemini_ocr_raw(encoded, mime_type, api_key)
        return jsonify({'success': True, 'extracted_text': text_out})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# STAGE 3 API: YOLOv8m-OBB COMPONENT & PIN DETECTION
# ==============================================================================

@app.route('/api/list_models', methods=['GET'])
def api_list_models():
    """Lists available PyTorch weights (.pt) files for object detection."""
    models = list_available_models(models_dir="models")
    return jsonify({'success': True, 'models': models})


@app.route('/api/run_yolo', methods=['POST'])
@app.route('/api/run_yolo_detection', methods=['POST'])
def api_run_yolo_detection():
    """
    Executes YOLO component detection and returns bounding boxes + annotated image.
    NOTE: This endpoint does NOT call Gemini/AI. It is pure YOLO inference only.
    Use /api/generate_hbom for the full pipeline (YOLO + Gemini OCR + HBoM table).
    """
    if not YOLO_AVAILABLE:
        return jsonify({'success': False, 'error': 'Ultralytics YOLO package not installed.'}), 530

    data = request.get_json(silent=True) or {}
    if 'image' not in data:
        return jsonify({'success': False, 'error': 'No image provided.'}), 400

    model_name   = data.get('model', 'model_yolov8m.pt')
    conf_thresh  = float(data.get('conf', DEFAULT_CONF_THRESH))
    iou_thresh   = float(data.get('iou', DEFAULT_IOU_THRESH))
    img_size     = int(data.get('imgsz', DEFAULT_IMG_SZ))
    # Visualisation toggles — controlled from the UI checkboxes
    show_boxes   = bool(data.get('show_boxes', True))
    show_labels  = bool(data.get('show_labels', True))
    show_conf    = bool(data.get('show_conf', True))

    try:
        img = decode_base64_image(data['image'])
        model = load_yolo_model(model_name)

        # Run YOLO inference only — no Gemini/AI calls here
        results = model(img, conf=conf_thresh, iou=iou_thresh, imgsz=img_size, verbose=False)
        res = results[0]

        # Speed metrics
        speed_raw = getattr(res, 'speed', {}) or {}
        speed_info = {
            'preprocess': round(float(speed_raw.get('preprocess', 5.0)), 1),
            'inference':  round(float(speed_raw.get('inference', 25.0)), 1),
            'postprocess': round(float(speed_raw.get('postprocess', 2.0)), 1)
        }

        # Annotated plot image — respects user's display toggle choices
        try:
            annotated_img_uri = encode_image_base64(
                res.plot(boxes=show_boxes, labels=show_labels, conf=show_conf),
                format_ext='.jpg'
            )
        except Exception:
            annotated_img_uri = data['image']

        names_dict = model.names if hasattr(model, 'names') else {}
        detections = []

        # Parse OBB or HBB boxes
        boxes_list = []
        if hasattr(res, 'obb') and res.obb is not None and len(res.obb) > 0:
            boxes_list = res.obb
        elif hasattr(res, 'boxes') and res.boxes is not None:
            boxes_list = res.boxes

        for i, box in enumerate(boxes_list):
            cls_id   = int(box.cls[0].cpu().numpy())
            cls_name = names_dict.get(cls_id, str(cls_id))
            conf     = float(box.conf[0].cpu().numpy())
            xyxy     = box.xyxy[0].cpu().numpy().tolist()
            crop_uri = crop_and_scale_component(img, xyxy, max_dim=250)

            detections.append({
                'id':           i + 1,
                'class':        cls_name,
                'class_name':   cls_name,
                'class_id':     cls_id,
                'confidence':   round(conf, 3),
                'box':          [round(c, 1) for c in xyxy],
                'bbox':         [round(c, 1) for c in xyxy],
                'crop':         crop_uri,
                'crop_image':   crop_uri,
                # Part info blank — use Generate HBoM for AI lookup
                'part_number':  '',
                'manufacturer': '',
                'logo_brand':   ''
            })

        return jsonify({
            'success':          True,
            'speed':            speed_info,
            'annotated_image':  annotated_img_uri,
            'total_components': len(detections),
            'detections':       detections
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate_hbom', methods=['POST'])
def api_generate_hbom():
    """
    Generates a structured Hardware Bill of Materials (HBoM) table combining YOLO
    component detections and Gemini LMM OCR extraction.
    """
    data = request.get_json(silent=True) or {}
    if 'image' not in data:
        return jsonify({'success': False, 'error': 'No image provided.'}), 400

    api_key = resolve_gemini_api_key(request)
    model_name = data.get('model', 'model_yolov8m.pt')
    conf_thresh = float(data.get('conf', DEFAULT_CONF_THRESH))
    iou_thresh  = float(data.get('iou', DEFAULT_IOU_THRESH))
    img_size    = int(data.get('imgsz', DEFAULT_IMG_SZ))

    try:
        img = decode_base64_image(data['image'])
        model = load_yolo_model(model_name)
        results = model(img, conf=conf_thresh, iou=iou_thresh, imgsz=img_size, verbose=False)
        res = results[0]

        annotated_img_uri = data['image']
        try:
            plotted_bgr = res.plot()
            annotated_img_uri = encode_image_base64(plotted_bgr, format_ext='.jpg')
        except Exception:
            pass

        names_dict = model.names if hasattr(model, 'names') else {}
        boxes_list = res.obb if (hasattr(res, 'obb') and res.obb is not None and len(res.obb) > 0) else (res.boxes if hasattr(res, 'boxes') else [])

        hbom_items = []
        class_counts = {}
        ic_crops = []
        ic_metadata = []

        ic_counter = 1
        for i, box in enumerate(boxes_list):
            cls_id = int(box.cls[0].cpu().numpy())
            cls_name = names_dict.get(cls_id, str(cls_id))
            conf = float(box.conf[0].cpu().numpy())
            xyxy = box.xyxy[0].cpu().numpy().tolist()

            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

            if cls_name.upper() in ['IC', 'ICS', 'CHIP'] or 'IC' in cls_name.upper():
                crop_uri = crop_and_scale_component(img, xyxy, max_dim=250)
                designator = f"U{ic_counter}"
                ic_counter += 1

                item = {
                    'designator': designator,
                    'part_number': 'SEARCHING...',
                    'manufacturer': 'GENERIC',
                    'category': 'Integrated Circuit',
                    'yolo_pins': '16-QFN',
                    'ocr_confidence': round(conf, 2),
                    'confidence_score': round(conf, 2),
                    'crop': crop_uri
                }
                hbom_items.append(item)
                if crop_uri:
                    ic_crops.append(crop_uri)
                    ic_metadata.append(len(hbom_items) - 1)

        # Batch Query Gemini OCR for IC crops
        if ic_crops and api_key:
            ocr_results = query_gemini_ocr_batch(ic_crops, api_key)
            for idx_in_ic, orig_idx in enumerate(ic_metadata):
                if idx_in_ic < len(ocr_results):
                    ocr = ocr_results[idx_in_ic]
                    hbom_items[orig_idx]['part_number'] = ocr.get('part_number', 'UNKNOWN')
                    hbom_items[orig_idx]['manufacturer'] = ocr.get('manufacturer', 'UNKNOWN')
                    if 'confidence' in ocr:
                        conf_val = float(ocr['confidence'])
                        hbom_items[orig_idx]['ocr_confidence'] = conf_val
                        hbom_items[orig_idx]['confidence_score'] = conf_val
        elif ic_crops and not api_key:
            for orig_idx in ic_metadata:
                hbom_items[orig_idx]['part_number'] = 'KEY_REQUIRED'
                hbom_items[orig_idx]['manufacturer'] = 'API Key Needed'

        summary_list = [{'component_class': k, 'class_name': k, 'quantity': v, 'designators': f"{k}1-{k}{v}"} for k, v in class_counts.items()]

        return jsonify({
            'success': True,
            'hbom': hbom_items,
            'summary': summary_list,
            'annotated_image': annotated_img_uri
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/detect_pins', methods=['POST'])
def api_detect_pins():
    """
    Runs IC Pin OBB Detection on detected microchip components.
    Detects ICs first, then crops each IC and executes the pin OBB model on it.
    Returns results list and base64 annotated image showing bold IC boxes and cyan oriented pin shapes.
    """
    if not YOLO_AVAILABLE:
        return jsonify({'success': False, 'error': 'YOLO package unavailable.'}), 530

    data = request.get_json(silent=True) or {}
    if 'image' not in data:
        return jsonify({'success': False, 'error': 'No image provided.'}), 400

    model_name = data.get('model', 'model_yolov8m.pt')
    conf_thresh = float(data.get('conf', DEFAULT_CONF_THRESH))
    iou_thresh  = float(data.get('iou', DEFAULT_IOU_THRESH))
    img_size    = int(data.get('imgsz', DEFAULT_IMG_SZ))
    pin_conf    = float(data.get('pin_conf', 0.20))

    try:
        img = decode_base64_image(data['image'])
        component_model = load_yolo_model(model_name)
        comp_results = component_model(img, conf=conf_thresh, iou=iou_thresh, imgsz=img_size, verbose=False)
        comp_res = comp_results[0]

        names_dict = component_model.names if hasattr(component_model, 'names') else {}
        boxes_list = comp_res.obb if (hasattr(comp_res, 'obb') and comp_res.obb is not None and len(comp_res.obb) > 0) else (comp_res.boxes if hasattr(comp_res, 'boxes') else [])

        annotated_pcb = img.copy()
        results_list = []
        ic_index = 0

        for box in boxes_list:
            cls_id = int(box.cls[0].cpu().numpy())
            cls_name = names_dict.get(cls_id, str(cls_id))
            if cls_name.upper() not in ['IC', 'ICS', 'CHIP'] and 'IC' not in cls_name.upper():
                continue

            ic_index += 1
            coords = box.xyxy[0].cpu().numpy().tolist()
            x1, y1, x2, y2 = [int(round(float(c))) for c in coords]
            
            # Crop directly for pin OBB detection to preserve full resolution/accuracy
            crop_bgr = img[max(0, y1):min(img.shape[0], y2), max(0, x1):min(img.shape[1], x2)]
            if crop_bgr.size == 0:
                continue

            pin_res = run_pin_detection_on_crop(crop_bgr, pin_model_path=PIN_MODEL_PATH, conf=pin_conf)
            pin_count = pin_res.get('pin_count', 0)
            pin_confidence = pin_res.get('confidence', 0.0)
            obb_boxes = pin_res.get('obb_boxes', [])

            # Draw IC bounding box (bold, thickness=4)
            cv2.rectangle(annotated_pcb, (x1, y1), (x2, y2), (255, 100, 0), 4)
            cv2.putText(annotated_pcb, f"U{ic_index} ({pin_count} Pins)", (x1, max(y1 - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 2, cv2.LINE_AA)

            # Draw individual pin OBBs (thickness=2)
            w_crop = x2 - x1
            h_crop = y2 - y1
            for pin_obb in obb_boxes:
                pts = []
                for i in range(0, 8, 2):
                    mx = x1 + pin_obb[i] * w_crop
                    my = y1 + pin_obb[i+1] * h_crop
                    pts.append([int(round(mx)), int(round(my))])
                pts = np.array(pts, np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated_pcb, [pts], isClosed=True, color=(0, 255, 255), thickness=2)

            results_list.append({
                'designator': f'U{ic_index}',
                'box': [round(c, 1) for c in coords],
                'pin_count': pin_count,
                'pin_confidence': pin_confidence
            })

        # Encode annotated image
        annotated_uri = encode_image_base64(annotated_pcb, format_ext='.jpg')

        return jsonify({
            'success': True,
            'ic_count': len(results_list),
            'results': results_list,
            'annotated_image': annotated_uri
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# STAGE 4 API: DISTANCE TRANSFORM POWER RAIL MAPPER
# ==============================================================================

@app.route('/api/detect_power_rails', methods=['POST'])
def api_detect_power_rails():
    """
    Executes Stage 4 Probe-Free Power Rail Identification via EDT trace width metrics
    and Gemini silkscreen label mapping.
    """
    data = request.get_json(silent=True) or {}
    if 'image' not in data:
        return jsonify({'success': False, 'error': 'No image provided.'}), 400

    api_key = resolve_gemini_api_key(request)
    width_thresh = float(data.get('trace_width_thresh', DEFAULT_POWER_TRACE_THRESH))

    try:
        img = decode_base64_image(data['image'])
        h, w = img.shape[:2]

        # 1. Convert to grayscale & segment copper traces
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, trace_mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 2. Compute Euclidean Distance Transform (EDT)
        width_map = compute_distance_transform_widths(trace_mask)

        # 3. Filter wide traces exceeding IPC-2221 conductor threshold
        wide_trace_mask = np.uint8(width_map >= width_thresh) * 255

        # 4. Find wide trace contours
        contours, _ = cv2.findContours(wide_trace_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 5. Query Gemini Flash for silkscreen labels
        silkscreen_labels = query_gemini_power_labels(data['image'], api_key) if api_key else []

        vcc_contours = []
        gnd_contours = []

        # Classify wide contours based on silkscreen proximity
        for cnt in contours:
            if cv2.contourArea(cnt) < 100:
                continue
            
            # Default classification by index/heuristic if no label
            label_assigned = False
            for lbl in silkscreen_labels:
                lx = int(lbl.get('center_x', 0) * w)
                ly = int(lbl.get('center_y', 0) * h)
                dist_to_cnt = cv2.pointPolygonTest(cnt, (lx, ly), True)
                if dist_to_cnt >= -50:  # within 50px of label
                    if lbl.get('type') == 'GND':
                        gnd_contours.append(cnt)
                    else:
                        vcc_contours.append(cnt)
                    label_assigned = True
                    break

            if not label_assigned:
                # Assign based on size threshold
                if cv2.contourArea(cnt) > 2000:
                    gnd_contours.append(cnt)
                else:
                    vcc_contours.append(cnt)

        svg_overlay = generate_power_rail_svg(w, h, vcc_contours, gnd_contours)

        # 6. Map silkscreen labels to VCC/GND labels output format for frontend table
        labels_response = []
        for lbl in silkscreen_labels:
            lx = int(lbl.get('center_x', 0) * w)
            ly = int(lbl.get('center_y', 0) * h)
            
            # Search nearby neighborhood in width_map for the maximum trace width
            x_min_nb = max(0, lx - 50)
            x_max_nb = min(w - 1, lx + 50)
            y_min_nb = max(0, ly - 50)
            y_max_nb = min(h - 1, ly + 50)
            
            neighborhood = width_map[y_min_nb:y_max_nb+1, x_min_nb:x_max_nb+1]
            local_max_width = float(np.max(neighborhood)) if neighborhood.size > 0 else 0.0
            
            labels_response.append({
                'text': lbl.get('label', 'PWR'),
                'type': lbl.get('type', 'VCC'),
                'x_pct': float(lbl.get('center_x', 0) * 100.0),
                'y_pct': float(lbl.get('center_y', 0) * 100.0),
                'trace_width_px': local_max_width if local_max_width > 0.0 else 6.0,
                'voltage': lbl.get('label', '') if lbl.get('type') == 'VCC' else None
            })

        # 7. Extract power regulators from the frontend's hbom payload
        hbom_list = data.get('hbom', [])
        power_ics = []
        for item in hbom_list:
            part_number = item.get('part_number', '').upper()
            category = item.get('category', '').upper()
            designator = item.get('designator', '')
            box = item.get('box') or item.get('bbox')
            
            is_power_ic = False
            if 'REGULATOR' in category or 'POWER' in category or 'PMIC' in category or 'LDO' in category:
                is_power_ic = True
            elif any(k in part_number for k in ['LM78', 'AMS1117', 'MAX1', 'MAX2', 'TPS', 'AP2112', 'MP2307', 'LM2596', 'LDO']):
                is_power_ic = True
            elif 'REGULATOR' in part_number or 'CONVERTER' in part_number:
                is_power_ic = True
                
            if is_power_ic and box:
                power_ics.append({
                    'designator': designator,
                    'part_number': item.get('part_number', 'Power Regulator'),
                    'box': box
                })

        # 8. Create annotated static image
        annotated_pcb = img.copy()
        cv2.drawContours(annotated_pcb, vcc_contours, -1, (0, 0, 255), 2)
        cv2.drawContours(annotated_pcb, gnd_contours, -1, (255, 0, 0), 2)
        
        for ic in power_ics:
            box = ic['box']
            bx1, by1, bx2, by2 = [int(round(float(c))) for c in box]
            cv2.rectangle(annotated_pcb, (bx1, by1), (bx2, by2), (0, 165, 255), 3)
            cv2.putText(annotated_pcb, f"{ic['designator']} ({ic['part_number']})", (bx1, max(by1 - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2, cv2.LINE_AA)

        annotated_img_uri = encode_image_base64(annotated_pcb, format_ext='.jpg')

        return jsonify({
            'success': True,
            'image_width': w,
            'image_height': h,
            'vcc_count': len(vcc_contours),
            'gnd_count': len(gnd_contours),
            'labels': labels_response,
            'power_ics': power_ics,
            'svg_overlay': svg_overlay,
            'annotated_image': annotated_img_uri
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# DATASHEET MINER & LLM PIN EXTRACTION API
# ==============================================================================

@app.route('/api/lookup_datasheet', methods=['POST'])
def api_lookup_datasheet():
    """Generates datasheet web queries for extracted IC part numbers."""
    data = request.get_json(silent=True) or {}
    part_num = data.get('part_number', '')
    api_key  = resolve_gemini_api_key(request)

    res = lookup_datasheet(part_num, api_key=api_key)
    return jsonify(res)


@app.route('/api/extract_power_pins', methods=['POST'])
def api_extract_power_pins():
    """Queries Gemini Flash to retrieve VCC/GND pinout mappings from part numbers."""
    data = request.get_json(silent=True) or {}
    part_num  = data.get('part_number', '')
    package   = data.get('package', 'SOIC-8')
    pin_count = int(data.get('pin_count', 8))
    api_key   = resolve_gemini_api_key(request)

    if not api_key:
        return jsonify({'success': False, 'error': 'Gemini API key is not configured.'}), 400

    res = extract_power_pins_llm(part_num, package=package, pin_count=pin_count, api_key=api_key)
    return jsonify({'success': True, 'pinout': res})


# ==============================================================================
# MAIN RUNTIME ENTRY POINT
# ==============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("  PCBRE: Optical Hardware Auditing & Reverse Engineering Server  ")
    print("=" * 70)
    print("  * Dashboard: http://localhost:5000")
    print("  * Stage 1 Substrate Tuner: http://localhost:5000/tuner/segmentation")
    print("  * Stage 2 OCR Tuner: http://localhost:5000/tuner/ocr")
    print("  * Stage 3 YOLO Detector: http://localhost:5000/detector/yolo")
    print("  * Stage 4 Power Net Mapper: http://localhost:5000/detector/power")
    print("  * Presentation Generator: http://localhost:5000/generate-ppt")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000, debug=True)