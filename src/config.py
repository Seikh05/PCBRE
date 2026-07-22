"""
PCBRE Configuration & API Key Resolution Module
=================================================
This module manages global app settings, environment variables, and 
dynamic Gemini API key resolution for the PCBRE runtime.

Key Precedence Order for Gemini API Keys:
    1. HTTP Request Header: 'X-Gemini-API-Key' (Passed from user Web UI)
    2. JSON Payload: 'api_key' or 'gemini_api_key'
    3. URL Query Parameter: 'api_key' or 'gemini_api_key'
    4. Environment Variable: GEMINI_API_KEY (from .env or OS environment)
"""

import os

def load_env_file(env_path=".env"):
    """
    Loads environment variables from a local `.env` file if present.
    Ignores commented lines (#) and strips quote marks.
    """
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")
            print(f"[INFO] Loaded environment variables from {env_path}")
        except Exception as e:
            print(f"[WARN] Failed to read {env_path}: {e}")

# Automatically load .env on import
load_env_file()


def resolve_gemini_api_key(request=None) -> str:
    """
    Dynamically resolves the Gemini API key for a request.

    Precedence:
      1. HTTP Header 'X-Gemini-API-Key'
      2. JSON body key 'api_key' or 'gemini_api_key'
      3. Query parameter 'api_key' or 'gemini_api_key'
      4. System environment variable 'GEMINI_API_KEY'

    Args:
        request (flask.Request, optional): Flask request object.

    Returns:
        str: Resolved Gemini API key string, or empty string if unconfigured.
    """
    if request:
        # 1. Check HTTP Headers
        header_key = request.headers.get("X-Gemini-API-Key")
        if header_key and header_key.strip():
            return header_key.strip()

        # 2. Check JSON payload
        if request.is_json:
            try:
                data = request.get_json(silent=True) or {}
                json_key = data.get("api_key") or data.get("gemini_api_key")
                if json_key and str(json_key).strip():
                    return str(json_key).strip()
            except Exception:
                pass

        # 3. Check Query Parameters
        query_key = request.args.get("api_key") or request.args.get("gemini_api_key")
        if query_key and query_key.strip():
            return query_key.strip()

    # 4. Fallback to Environment Variable
    return os.environ.get("GEMINI_API_KEY", "").strip()


# Directory Configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR = os.path.join(BASE_DIR, "models")
PIN_MODEL_PATH = os.path.join(MODELS_DIR, "ic_pin_yolo.pt")

# Default Parameters
DEFAULT_CONF_THRESH = 0.25
DEFAULT_IOU_THRESH = 0.45
DEFAULT_IMG_SZ = 1024
DEFAULT_POWER_TRACE_THRESH = 6.0  # pixels
