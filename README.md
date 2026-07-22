<div align="center">

# PCBRE: Multi-Modal Hardware Auditing & Reverse Engineering Framework

**Non-Destructive PCB Assurance, Oriented Component Detection, LMM OCR, and Probe-Free Power Rail Mapping**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Ultralytics YOLOv8](https://img.shields.io/badge/YOLOv8-OBB-00FFFF.svg)](https://docs.ultralytics.com/)
[![Google Gemini LMM](https://img.shields.io/badge/Gemini_1.5-Flash_LMM-4285F4.svg)](https://ai.google.dev/)
[![Flask Web UI](https://img.shields.io/badge/Flask-Web_UI-000000.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Developed at Department of Electronic Systems Engineering (DESE), Indian Institute of Science (IISc), Bengaluru*  
*IASc-INSA-NASI Summer Research Fellowship Programme (2026)*

---

</div>

## 📌 Executive Summary

**PCBRE** is an offline, non-destructive, multi-modal optical framework designed for hardware security assurance, automated Hardware Bill of Materials (HBoM) extraction, and probe-free power rail mapping directly from high-resolution Printed Circuit Board (PCB) surface photography.

---

## ❓ WHY? (Motivation & Problem Statement)

### The Hardware Security Imperative
Globalized semiconductor manufacturing relies on multi-vendor supply chains across un-trusted Fab environments. This geographic dispersal introduces critical vulnerability windows where adversarial actors can inject **Hardware Trojans**, substitute counterfeit microchips, or modify physical PCB trace layouts prior to system deployment.

```
                    PHYSICAL PCB SUPPLY CHAIN THREAT VECTOR
 [IC Design (Fab)] ──> [Board Assembly (EMS)] ──> [Untrusted Transit] ──> [Field Deployment]
                               │                                               │
                               ▼                                               ▼
                     [Counterfeit Chips /]                           [Hardware Trojan /]
                     [Sub-standard Swaps ]                           [Unverified Netlist]
```

### Limitations of State-of-the-Art (SOTA) Methods
Existing hardware reverse engineering techniques exhibit severe operational constraints:

1. **Chemical De-Layering (Destructive):** Requires concentrated Nitric ($HNO_3$) and Hydrofluoric ($HF$) acids to etch solder masks. It is toxic, hazardous, expensive, and **permanently destroys the target board**.
2. **Contact-Based Robotic Probing (PROBoter):** Requires sub-millimeter robotic arm alignment to physically probe copper traces. It is slow, highly susceptible to mechanical trace damage, and cannot probe under BGA (Ball Grid Array) components.
3. **CAD-Dependent Graph Verification (VIPR-PCB):** Relies strictly on pre-existing Altium or KiCAD netlists. In black-box hardware auditing, original CAD files are almost never available.

### The PCBRE Solution
PCBRE introduces a **purely optical, non-destructive audit pipeline**. It combines **Oriented Bounding Box (OBB) Deep Learning**, **Large Multimodal Vision Models (Gemini 1.5 Flash)**, and **Euclidean Distance Transform (EDT) Trace Metrics** to extract component part numbers, pin counts, and power net topologies without physical probing or board destruction.

---

## 💡 WHAT? (System Architecture & Pipeline Features)

PCBRE structures the reverse engineering process into 4 modular stages, separating classical baseline preprocessing from our proposed deep-learning methodology:

```
                                 PCBRE PIPELINE ARCHITECTURE
                                 
  [ Raw PCB Image ]
         │
         ├───► CLASSICAL BASELINES (Heuristic Preprocessing)
         │      ├── Stage 1: Classical Substrate HSV Masking & Morphological Filter
         │      └── Stage 2: CLAHE Contrast + Gaussian Unsharp Edge Masking
         │
         └───► PROPOSED METHODOLOGY (Our Core Architecture)
                ├── Stage 3: YOLOv8m-OBB (Oriented Component Localization at 1024px)
                ├── Cloud LMM: Gemini 1.5 Flash (Zero-Shot Alphanumeric Chip OCR)
                └── Stage 4: Distance Transform Trace Profiling + IPC-2221 Power Mapper
```

### Key Stage Breakdown:

| Stage | Module Name | Algorithm / Principle | Purpose / Output |
| :--- | :--- | :--- | :--- |
| **Stage 1** | Substrate HSV Segmentation | Color-Space Decoupling ($H, S, V$) & Morphology ($\circ, \bullet$) | Isolates background resin substrate from foreground copper pads/chips. |
| **Stage 2** | Local OCR Preprocessing | CLAHE ($8\times 8$ tiles) + Gaussian Unsharp Masking ($g = f + \alpha g_{\text{mask}}$) | Enhances degraded, laser-etched alphanumeric text on chip packages. |
| **Stage 3** | YOLOv8m-OBB Detector | 5-Param Bounding Boxes $b = \{x_c, y_c, w, h, \theta\}$ at $1024\times 1024$ px | Rotation-invariant component & pin detection ($0.749\text{ mAP@0.5}$). |
| **LMM Engine** | Gemini 1.5 Flash OCR | Zero-Shot Contextual Vision Attention + Part Naming Heuristics | Solves suffix truncation (`STM32F745VGT6`) & extracts structured JSON HBoM. |
| **Stage 4** | Probe-Free Power Mapper | Euclidean Distance Transform $D(p) = \min_{q \in B^c} \|p-q\|_2$ + IPC-2221 | Identifies VCC & GND rails by trace width profiling ($\ge 6.0\text{px}$) & silkscreen matching. |

---

## 🛠️ HOW? (Installation, Quickstart & Usage)

### 1. Prerequisites
- **Python:** Version `3.10` or higher
- **Git:** Version `2.30+`
- **Optional:** NVIDIA GPU with CUDA for accelerated YOLO inference.

### 2. Environment Setup & Installation

Clone the repository and set up a virtual environment:

```bash
# Clone repository
git clone https://github.com/Seikh05/PCBRE.git
cd PCBRE

# Create and activate Python virtual environment
python -m venv venv

# On Windows PowerShell:
.\venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Gemini API Key Setup

Gemini 1.5 Flash powers the cloud LMM OCR and silkscreen label parsing. You can configure your API key in **two flexible ways**:

#### Option A: Web UI Input Bar (Recommended for Deployment)
Launch the web application and paste your API key directly into the top **🔑 API Key** bar in the dashboard. The key is verified live and saved safely in your browser's `localStorage`.

#### Option B: Environment File (`.env`)
Create a `.env` file in the project root directory:

```env
GEMINI_API_KEY=AIzaSyYourActualGeminiApiKeyHere
```

### 4. Training Datasets & Sources

| Model Target | Dataset Source & Link | Format | Usage |
| :--- | :--- | :--- | :--- |
| **IC Pin Detection Model** | [PROBoter Schutzwerk Image Dataset](https://github.com/schutzwerk/PROBoter/tree/master/image_data_sets) | YOLO OBB | Training IC Pin OBB detector (`models/ic_pin_yolo.pt`). |
| **Component Detection Model** | [PCB Component Detection Dataset](https://universe.roboflow.com/research-pbbdl/pcb-component-detection-dre7a) (Roboflow Universe) | YOLOv8 OBB | Training YOLOv8m-OBB component model (`models/model_yolov8m.pt`). |
| **Interface Port Detection** | [PCB Port Detection Dataset](https://universe.roboflow.com/) (Roboflow Universe) | YOLOv8 | Training Interface Port detector (`models/detect_port_yolov8n.pt`). |

All processed training and validation dataset files (images and text annotations) are also available as a single consolidated download in the following Google Drive folder:
👉 **[Google Drive Datasets Folder](https://drive.google.com/drive/folders/1nlvSOsw8zFBidwPpoBRWWKkTZmnqB16A?usp=sharing)**


### 5. Pretrained Model Weights Setup

All pretrained YOLO neural network weights are hosted and available for direct download in the following Google Drive folder:
👉 **[Google Drive Model Weights Folder](https://drive.google.com/drive/folders/1_unD3NbQUPcl_qx1C39opS397JGCPxYu?usp=drive_link)**

#### Downloading and Placement Instructions:
1. Access the Google Drive link above.
2. Download all three model files:
   - `model_yolov8m.pt` (Trained YOLOv8m-OBB component model - **Recommended**, 50.8 MB)
   - `ic_pin_yolo.pt` (Trained IC Pin OBB model, 6.6 MB)
   - `detect_port_yolov8n.pt` (Trained Interface Port detector model, 6.7 MB)
3. Create a folder named `models` in the root of the cloned `PCBRE` project directory if it does not already exist.
4. Move the downloaded `.pt` weight files into the `models/` directory:
   ```text
   PCBRE/
   └── models/
       ├── model_yolov8m.pt
       ├── ic_pin_yolo.pt
       └── detect_port_yolov8n.pt
   ```

> *Note: Large model weight binaries (`.pt`) and local cache files are excluded via `.gitignore` to keep the source repository clean and lightweight.*

### 6. Running the Application

Launch the Flask web server:

```bash
python app.py
```

Open your browser and navigate to:
* **Dashboard Homepage:** `http://localhost:5000`
* **Stage 1 HSV Substrate Tuner:** `http://localhost:5000/tuner/segmentation`
* **Stage 2 OCR Preprocessing Tuner:** `http://localhost:5000/tuner/ocr`
* **Stage 3 YOLO Component Detector:** `http://localhost:5000/detector/yolo`
* **Stage 4 Power Net Mapper:** `http://localhost:5000/detector/power`
* **Presentation Generator:** `http://localhost:5000/generate-ppt`

---

## 🔬 Experimental Jupyter Notebooks Reference

All research experiments and model training pipelines are documented in the `notebooks/` directory:

| Notebook | Focus Area & Description |
| :--- | :--- |
| **[01_IC_Pin_Detection_PROBoter_YOLOv8_OBB.ipynb](notebooks/01_IC_Pin_Detection_PROBoter_YOLOv8_OBB.ipynb)** | IC Pin OBB model training using Schutzwerk PROBoter dataset. |
| **[02_Component_Detection_YOLOv8m_OBB.ipynb](notebooks/02_Component_Detection_YOLOv8m_OBB.ipynb)** | YOLOv8m-OBB component detector training ($1024\times 1024$ resolution). |
| **[03_Interface_Port_Detection_YOLOv8n.ipynb](notebooks/03_Interface_Port_Detection_YOLOv8n.ipynb)** | Interface Port detection model training on Roboflow port dataset. |
| **[04_PCBRE_End_To_End_Pipeline_Exploration.ipynb](notebooks/04_PCBRE_End_To_End_Pipeline_Exploration.ipynb)** | End-to-end pipeline evaluation and baseline HSV/CLAHE experiments. |

---

## 📊 Experimental Results & Performance

Validation metrics across YOLOv8-OBB model configurations trained at $1024\times 1024$ resolution:

| Target Class | Validation Instances | YOLOv8n-OBB (mAP@0.5) | YOLOv8s-OBB (mAP@0.5) | YOLOv8m-OBB (mAP@0.5) |
| :--- | :---: | :---: | :---: | :---: |
| **All Classes** | **979** | **0.445** | **0.569** | **0.749** (+30.4%) |
| **ICs (Microchips)** | 45 | 0.772 | 0.850 | 0.732 |
| **Capacitors** | 508 | 0.553 | 0.721 | **0.785** |
| **Resistors** | 401 | 0.127 | 0.414 | **0.581** |

---

## 📁 Repository Directory Architecture

```
PCBRE/
├── app.py                      # Main Flask Web Server & REST API Routes
├── requirements.txt            # Python Dependencies Specification
├── .gitignore                  # Git Exclusion Rules (ignoring venv, secrets, .pt weights)
├── .env                        # Local Environment Variables (API Keys)
├── generate_ppt.js             # Node.js PptxGenJS CLI Slide Generator
├── generate_presentation.html  # Standalone PowerPoint Generator
├── Internship_Report.tex       # Complete Academic Internship LaTeX Report
│
├── notebooks/                  # Formatted Research Notebooks
│   ├── 01_IC_Pin_Detection_PROBoter_YOLOv8_OBB.ipynb
│   ├── 02_Component_Detection_YOLOv8m_OBB.ipynb
│   ├── 03_Interface_Port_Detection_YOLOv8n.ipynb
│   └── 04_PCBRE_End_To_End_Pipeline_Exploration.ipynb
│
├── src/                        # Modular Python Package
│   ├── __init__.py             # Package Initializer & Metadata
│   ├── config.py               # Settings & Dynamic API Key Resolution
│   ├── stage1_segmentation.py  # Substrate HSV Masking & Morphology
│   ├── stage2_ocr.py           # CLAHE, Unsharp Masking & Gemini LMM OCR
│   ├── stage3_yolo.py          # YOLOv8m-OBB Detector & Crop Exporter
│   ├── stage4_power.py         # Distance Transform Trace Profiler & Power Mapper
│   ├── datasheet_miner.py      # Datasheet Search & LLM Pin Mapping
│   └── utils.py                # Base64 Converters & JSON Sanitizers
│
├── templates/                  # HTML5 Web UI Templates
│   ├── dashboard.html          # Main Workspace Dashboard
│   ├── stage1_tuner.html       # HSV Segmenter View
│   ├── stage2_ocr.html         # OCR Sharpening View
│   ├── stage3_yolo.html        # YOLO & LMM HBoM View
│   ├── stage4_power.html       # Power Net SVG Overlay View
│   └── generate_presentation.html
│
├── static/                     # Static Web Assets (CSS, JS, Sample Images)
└── models/                     # PyTorch Weights Directory (.gitkeep)
```

---

## 📄 License & Academic Citation

This project is released under the [MIT License](LICENSE).

If you use PCBRE in your academic research or hardware security auditing, please cite:

```bibtex
@techreport{mustakim2026pcbre,
  title={PCBRE: A Multi-Modal Hardware Auditing & Reverse Engineering Framework},
  author={Mustakim, Seikh Souvagya and Dagale, Haresh},
  institution={Department of Electronic Systems Engineering (DESE), Indian Institute of Science (IISc), Bengaluru},
  year={2026},
  note={IASc-INSA-NASI Summer Research Fellowship Programme}
}
```