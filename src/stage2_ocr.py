"""
Stage 2: OCR Preprocessing & LMM Extraction Module
===================================================
This module provides localized image contrast enhancement (CLAHE), high-frequency
edge sharpening (Gaussian Unsharp Masking), and cloud-based Large Multimodal Model
(Gemini 1.5 Flash) OCR extraction for reading degraded, laser-etched IC package text.

Mathematical Formulations:
--------------------------
1. Contrast Limited Adaptive Histogram Equalization (CLAHE):
   Calculates local histograms over small contextual image tiles (typically 8x8 pixels).
   Histogram height is clipped at threshold C to prevent noise amplification over flat chip bodies:
       H_clipped(v) = min(H(v), C)
   The redistributed excess contrast restores degraded laser-etched text uniformly.

2. Gaussian Unsharp Masking:
   Generates a high-frequency detail mask by subtracting a Gaussian-blurred version of image f:
       g_mask(x, y) = f(x, y) - (G_sigma * f)(x, y)
   Re-combines the scaled mask with original f to sharpen alphanumeric character edges:
       g(x, y) = f(x, y) + alpha * g_mask(x, y)
   Setting sigma = 1.0 and alpha in [1.0, 2.0] substantially enhances OCR read rates.

3. Gemini LMM Attention vs Local OCR (Domain Shift Justification):
   Local OCR engines (PaddleOCR, EasyOCR) treat chip text as document lines, often truncating
   part number suffixes (e.g. reading 'STM32F745VGT6' as 'STM32F745'). Gemini 1.5 Flash integrates
   visual features with deep prior semantic knowledge of semiconductor naming conventions,
   recovering complete part numbers and manufacturer metadata zero-shot.
"""

import time
import json
import requests
import cv2
import numpy as np
from src.utils import encode_image_base64, sanitize_json_response

# Prompt Constants
SINGLE_IC_PROMPT = """You are an expert electronics engineer performing PCB reverse engineering.
Analyze this cropped image of an IC chip package and extract:

1. PART NUMBER: The main IC identifier (e.g. STM32F745VGT6, FT2232H-56Q, MAX3421EE).
   RULES:
   - NOT the batch/date code (4-digit YYWW like 2349, V632)
   - NOT country of manufacture (MEXICO, CHINA, PHIL, INDIA)
   - NOT the manufacturer name alone
   - Text may be rotated 90/180/270 degrees — still read it
   - If partial, give best guess
   - If truly unreadable, return UNKNOWN

2. MANUFACTURER: Company name (STMicroelectronics, FTDI, Maxim Integrated, Texas Instruments, NXP, Microchip, etc.)
3. LOGO_BRAND: Short brand mark (ST, FTDI, TI, NXP, etc.)
4. CONFIDENCE_SCORE: 0.0 to 1.0 — how confident are you in the part number extraction
5. RAW_TEXT: All text visible on the chip exactly as seen"""

BATCH_IC_PROMPT_OBJECT = """You are an expert electronics engineer performing PCB reverse engineering.
I am sending you {n} cropped IC chip images.

For EACH image extract:
1. part_number: Main IC identifier. NOT batch codes (YYWW format), NOT country names. Text may be rotated — still read it. Return UNKNOWN only if truly unreadable.
2. manufacturer: Full company name
3. logo_brand: Short brand (ST, TI, FTDI, etc.)
4. confidence_score: 0.0-1.0
5. raw_text: All visible text on chip

Return a JSON object with a single key 'results' containing a JSON array of exactly {n} objects — one per image in order.
If an image is not an IC (connector, crystal, mechanical part), set part_number to NOT_IC.

Each object in the 'results' array MUST contain exactly these 5 keys:
- "part_number": (string, e.g. "STM32F103C8T6", "UNKNOWN", or "NOT_IC")
- "manufacturer": (string, e.g. "STMicroelectronics" or "UNKNOWN")
- "logo_brand": (string, e.g. "ST" or "UNKNOWN")
- "confidence_score": (float, e.g. 0.9)
- "raw_text": (string, e.g. "STM32F103...")

CRITICAL FORMATTING RULES:
1. Return ONLY the raw JSON object starting with {{ and ending with }}.
2. Do NOT wrap the output in markdown code blocks (do NOT use ```json or ```).
3. Do NOT include any conversational text, notes, or preamble. Just the raw JSON."""


def apply_clahe(img: np.ndarray, clip_limit: float = 3.0, tile_grid_size: int = 8) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) to an image.

    Args:
        img (np.ndarray): Input BGR or Grayscale OpenCV image.
        clip_limit (float): Threshold for contrast limiting.
        tile_grid_size (int): Size of grid for histogram equalization (e.g. 8x8).

    Returns:
        np.ndarray: Contrast-enhanced image matrix.
    """
    if len(img.shape) == 3:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    else:
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size))
        return clahe.apply(img)


def apply_unsharp_mask(img: np.ndarray, sigma: float = 1.0, alpha: float = 1.5) -> np.ndarray:
    """
    Applies Gaussian Unsharp Masking to sharpen high-frequency character edges.
    Formula: g(x,y) = f(x,y) + alpha * (f(x,y) - G_sigma * f(x,y))

    Args:
        img (np.ndarray): Input BGR or Grayscale image.
        sigma (float): Gaussian blur standard deviation.
        alpha (float): Scaling factor for edge enhancement.

    Returns:
        np.ndarray: Edge-sharpened image matrix.
    """
    blurred = cv2.GaussianBlur(img, (0, 0), sigma)
    sharpened = cv2.addWeighted(img, 1.0 + alpha, blurred, -alpha, 0)
    return sharpened


def query_gemini_ocr_raw(encoded_image: str, mime_type: str, api_key: str, max_retries: int = 5) -> str:
    """
    Queries Gemini 1.5 Flash for OCR extraction on a single IC image with retries & backoff.

    Args:
        encoded_image (str): Raw Base64 string (without data URI prefix).
        mime_type (str): MIME type (e.g., 'image/jpeg').
        api_key (str): Gemini API key.
        max_retries (int): Retry attempts for 429 rate limit errors.

    Returns:
        str: Raw text extracted by Gemini model.
    """
    if not api_key:
        raise ValueError("Gemini API key is not configured.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": SINGLE_IC_PROMPT},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": encoded_image
                    }
                }
            ]
        }]
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=25)
            if response.status_code == 200:
                res_data = response.json()
                try:
                    return res_data['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError):
                    return "[ERROR] Could not parse text from Gemini response structure."
            elif response.status_code == 429:
                retry_delay = 2.0 ** attempt
                print(f"[WARN] Gemini 429 rate limit hit. Retrying in {retry_delay:.1f}s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                print(f"[ERROR] Gemini request failed with status {response.status_code}: {response.text}")
                time.sleep(1.5)
        except Exception as e:
            print(f"[WARN] Gemini query exception: {str(e)}. Retrying...")
            time.sleep(1.5)

    return "[ERROR] Gemini API request failed after maximum retries (Rate Limit / Network Issue)."


def query_gemini_ocr_batch(crops_list: list, api_key: str, chunk_size: int = 3, max_retries: int = 5) -> list:
    """
    Sends cropped IC images in small chunks (e.g. 3 crops at a time) to Gemini Flash
    to avoid triggering 1M TPM rate limit errors.

    Args:
        crops_list (list): List of Base64 image URIs.
        api_key (str): Gemini API key.
        chunk_size (int): Number of crops per API request. Default 3.
        max_retries (int): Maximum retries on rate limits.

    Returns:
        list: Extracted JSON objects for all crops.
    """
    if not api_key:
        raise ValueError("Gemini API key is not configured.")

    results_all = []

    for i in range(0, len(crops_list), chunk_size):
        chunk = crops_list[i:i + chunk_size]
        print(f"[INFO] Sending chunk of {len(chunk)} crops to Gemini (indices {i} to {i + len(chunk) - 1})...")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"

        prompt = BATCH_IC_PROMPT_OBJECT.format(n=len(chunk))
        parts = [{"text": prompt}]

        for crop_uri in chunk:
            if ',' in crop_uri:
                mime_part, encoded = crop_uri.split(',', 1)
                mime_type = mime_part.split(';')[0].split(':')[1]
            else:
                encoded = crop_uri
                mime_type = "image/jpeg"

            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": encoded
                }
            })

        payload = {"contents": [{"parts": parts}]}
        success = False

        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    res_data = response.json()
                    text_out = res_data['candidates'][0]['content']['parts'][0]['text']
                    parsed = sanitize_json_response(text_out)

                    # Extract results list from response
                    if isinstance(parsed, dict) and 'results' in parsed:
                        chunk_results = parsed['results']
                    elif isinstance(parsed, list):
                        chunk_results = parsed
                    else:
                        chunk_results = [parsed]

                    results_all.extend(chunk_results)
                    success = True
                    break
                elif response.status_code == 429:
                    backoff = 2.0 ** attempt
                    print(f"[WARN] Gemini chunk 429 rate limit hit. Retrying in {backoff:.1f}s...")
                    time.sleep(backoff)
                else:
                    print(f"[ERROR] Gemini chunk query failed status {response.status_code}: {response.text}")
                    time.sleep(2.0)
            except Exception as e:
                print(f"[WARN] Gemini chunk query exception: {str(e)}")
                time.sleep(2.0)

        if not success:
            # Fallback objects if query failed
            for _ in chunk:
                results_all.append({
                    "part_number": "UNKNOWN",
                    "manufacturer": "UNKNOWN",
                    "logo_brand": "UNKNOWN",
                    "confidence_score": 0.0,
                    "raw_text": "API_RATE_LIMIT_ERROR"
                })

    return results_all
