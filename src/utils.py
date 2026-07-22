"""
PCBRE Utilities & Helper Functions
===================================
Provides shared utilities for Base64 image decoding/encoding, image cropping,
JSON schema parsing/sanitization, and bounding box math.
"""

import base64
import json
import re
import cv2
import numpy as np


def decode_base64_image(base64_str: str) -> np.ndarray:
    """
    Decodes a Base64 data URI string into an OpenCV BGR numpy array.

    Args:
        base64_str (str): Base64 data URI string (e.g. 'data:image/jpeg;base64,...').

    Returns:
        np.ndarray: OpenCV BGR image array.

    Raises:
        ValueError: If decoding fails or image format is invalid.
    """
    if ',' in base64_str:
        header, encoded = base64_str.split(',', 1)
    else:
        encoded = base64_str

    img_bytes = base64.b64decode(encoded)
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Failed to decode image: cv2.imdecode returned None.")

    return img


def encode_image_base64(img: np.ndarray, format_ext: str = ".jpg") -> str:
    """
    Encodes an OpenCV BGR numpy image array into a Base64 data URI string.

    Args:
        img (np.ndarray): OpenCV image matrix.
        format_ext (str): Compression format (e.g., '.jpg', '.png').

    Returns:
        str: Base64 data URI string suitable for HTML/JSON transport.
    """
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }
    mime_type = mime_map.get(format_ext.lower(), "image/jpeg")
    _, buffer = cv2.imencode(format_ext, img)
    encoded = base64.b64encode(buffer).decode('utf-8')
    return f"data:{mime_type};base64,{encoded}"


def crop_and_scale_component(img: np.ndarray, coords: list, max_dim: int = 250) -> str:
    """
    Crops a rectangular area out of an OpenCV image and scales it down to max_dim pixels.

    Scaling crops to max_dim (e.g., 250px) is critical for cloud LMMs (Gemini Flash)
    to prevent triggering TPM (Tokens Per Minute) 429 rate limit errors while
    preserving alphanumeric package text readability.

    Args:
        img (np.ndarray): Full PCB image matrix.
        coords (list): Bounding box coordinates [x1, y1, x2, y2].
        max_dim (int): Maximum width or height constraint in pixels.

    Returns:
        str: Base64 data URI of the cropped & scaled component image, or None if crop invalid.
    """
    try:
        h, w = img.shape[:2]
        x1, y1, x2, y2 = [int(round(float(c))) for c in coords]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        if x2 > x1 and y2 > y1:
            crop = img[y1:y2, x1:x2]
            hc, wc = crop.shape[:2]

            # Scale down if crop exceeds max_dim
            if max(hc, wc) > max_dim:
                scale = max_dim / float(max(hc, wc))
                new_w = max(1, int(wc * scale))
                new_h = max(1, int(hc * scale))
                crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)

            return encode_image_base64(crop, format_ext=".jpg")
    except Exception as e:
        print(f"[WARN] Failed to crop component coords {coords}: {str(e)}")
    return None


def sanitize_json_response(raw_text: str):
    """
    Strips markdown code blocks (```json ... ```) and leading/trailing whitespace
    to parse clean JSON from LLM responses.

    Args:
        raw_text (str): Raw string output from LLM.

    Returns:
        dict or list: Parsed JSON Python object.
    """
    cleaned = raw_text.strip()
    # Remove markdown code fence if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    return json.loads(cleaned)
