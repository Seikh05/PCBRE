import os
import sys
import base64
import argparse
import requests
import json

def encode_image(image_path):
    """Encodes a local image to base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"[ERROR] Failed to read/encode image: {str(e)}")
        sys.exit(1)

def query_gemini_ocr(image_path, api_key):
    """Sends the image to Google Gemini API for structured OCR extraction."""
    base64_data = encode_image(image_path)
    
    # Determine mime type based on extension
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = "image/jpeg"
    if ext == ".png":
        mime_type = "image/png"
    elif ext == ".bmp":
        mime_type = "image/bmp"
    elif ext == ".webp":
        mime_type = "image/webp"

    # API Endpoint (using stable Gemini Flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    # Request headers
    headers = {
        "Content-Type": "application/json"
    }

    # Request payload enforcing structured JSON schema output
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are an expert hardware engineer. Examine this cropped optical image of "
                            "a PCB integrated circuit (IC) package. Extract the printed part number, "
                            "brand/manufacturer name, and any identified logo markings. "
                            "If part of the text is obscured or blurry, make your best logical engineering guess."
                        )
                    },
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "part_number": {
                        "type": "STRING", 
                        "description": "The exact alphanumeric model/part number of the chip (e.g. STM32F051C8T6)"
                    },
                    "manufacturer": {
                        "type": "STRING", 
                        "description": "The name of the semiconductor manufacturer (e.g. STMicroelectronics)"
                    },
                    "logo_brand": {
                        "type": "STRING",
                        "description": "The logo or brand emblem visible on the package (e.g. ST logo, Texas Instruments logo)"
                    },
                    "confidence_score": {
                        "type": "NUMBER",
                        "description": "Your confidence in the extracted values between 0.0 and 1.0"
                    }
                },
                "required": ["part_number", "manufacturer"]
            }
        }
    }

    print(f"[INFO] Sending request to Gemini Flash API (via gemini-flash-latest) for: {os.path.basename(image_path)}...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Check HTTP response code
        if response.status_code != 200:
            print(f"[ERROR] API Request failed (Status Code: {response.status_code})")
            print(response.text)
            return None
            
        response_data = response.json()
        
        # Extract text candidate from the response structure
        candidates = response_data.get("candidates", [])
        if not candidates:
            print("[WARN] No prediction candidates returned from Gemini.")
            return None
            
        content_text = candidates[0]["content"]["parts"][0]["text"]
        
        # Parse the JSON string from Gemini
        extracted_data = json.loads(content_text)
        return extracted_data
        
    except requests.exceptions.RequestException as req_err:
        print(f"[ERROR] Network connection failed: {str(req_err)}")
        return None
    except json.JSONDecodeError as json_err:
        print(f"[ERROR] Failed to parse JSON returned from Gemini: {str(json_err)}")
        print("Raw response text:", content_text)
        return None
    except KeyError as key_err:
        print(f"[ERROR] Unexpected response format from API: {str(key_err)}")
        print("Raw response:", response_data)
        return None

def load_env_file():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

def main():
    parser = argparse.ArgumentParser(description="Extract IC text data using Google Gemini Multimodal API.")
    parser.add_argument("--image", required=True, help="Path to the cropped IC image file.")
    parser.add_argument("--key", help="Google AI Studio API Key. If not provided, GEMINI_API_KEY environment variable will be used.")
    
    args = parser.parse_args()
    
    # Load .env file if available
    load_env_file()
    
    # Resolve API Key
    api_key = args.key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] No Google Gemini API key found.")
        print("Provide it using --key or set the GEMINI_API_KEY environment variable.")
        sys.exit(1)
        
    if not os.path.exists(args.image):
        print(f"[ERROR] Image path does not exist: {args.image}")
        sys.exit(1)
        
    result = query_gemini_ocr(args.image, api_key)
    
    if result:
        print("\n--- Extraction Successful ---")
        print(json.dumps(result, indent=4))
    else:
        print("\n[ERROR] Extraction failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
