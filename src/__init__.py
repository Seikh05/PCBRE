"""
PCBRE: Multi-Modal Hardware Auditing & PCB Reverse Engineering Package
========================================================================
This package provides a modular, 4-stage pipeline for automated optical
PCB reverse engineering, hardware bill of materials (HBoM) extraction,
and probe-free power rail identification.

Modules:
    - config: Configuration, environment variables, and API key resolution.
    - utils: Base64 decoding, image conversion, geometry math, JSON helpers.
    - stage1_segmentation: HSV Substrate Segmentation & Morphological Filtering.
    - stage2_ocr: CLAHE, Unsharp Masking, and Gemini LMM OCR engine.
    - stage3_yolo: YOLOv8-OBB Oriented Component & Pin Detection.
    - stage4_power: Distance Transform Trace Profiling & Power Rail Mapping.
    - datasheet_miner: Automated datasheet mining & LLM pin extraction.
"""

__version__ = "1.0.0"
__author__ = "Seikh Souvagya Mustakim"
