# Comprehensive Literature Review: Optical PCB Reverse Engineering & Assurance
**Project**: Optical PCB Reverse Engineering (PCBRE)  
**Date**: July 8, 2026  
**Subject**: Synthesized review of all papers in the `literatures/` directory, mapping visual detection, character recognition, schematic reconstruction, and dataset targets.

---

## 📖 Papers Evaluated
1. **FPIC**: *FPIC: A Novel Semantic Dataset for Optical PCB Assurance* (Jessurun et al., 2023)
2. **ICText**: *When IC meets text: Towards a rich annotated integrated circuit text dataset* (Ng et al., 2024)
3. **FICS-PCB**: *FICS-PCB: A Multi-Modal Image Dataset for Automated Printed Circuit Board Visual Inspection* (Lu et al., 2020)
4. **WOOT17**: *Automated PCB Reverse Engineering* (Kleber et al., WOOT 2017)
5. **VIPR-PCB**: *VIPR-PCB: A Machine Learning based Golden-Free PCB Assurance Framework* (Bhattacharyay et al., 2022)
6. **PROBoter**: *PROBoter - Automating PCB analysis tasks to support penetration tests of embedded systems* (Weber et al., 2021)

---

## 🔍 Key Domain Syntheses

### 1. IC Text OCR (Optical Character Recognition)
*   **The Problem (ICText, WOOT17)**: 
    Off-the-shelf natural scene OCR (e.g. models trained on street views/documents) fails on ICs due to:
    1.  **Non-semantic content**: Batch codes, serial numbers, and part numbers do not follow language dictionary models. Recurrent text sequence decoders (like CRNN) get confused.
    2.  **Specular distortion**: Specular sheen from conformal coating and glare under direct lighting (FICS-PCB).
    3.  **Defective character types**: Broken, low-contrast, or out-of-focus prints (ICText).
*   **The Solutions & Clues**:
    *   **Character-Level Segmentation (ICText)**: Word-level text spotters (like EAST, DB, ABCNet) struggle because IC text lacks standard word spacing. Segmenting and classifying character-by-character yields higher accuracy.
    *   **Orientation Normalization (FPIC)**: Text markings rotate from $0^\circ$ to $359^\circ$. Rotated sub-images must be geometrically aligned horizontally before feeding into the OCR engine.
    *   **Contrast Inversion (WOOT17)**: Since IC text is white-on-black, inverting the image patch to black-on-white matches standard OCR pre-training formats, boosting recognition accuracy.
    *   **Logo Removal (WOOT17)**: Manufacturer logos obstruct reading. Filter them out using template libraries or custom CNN classifiers before text recognition.

---

### 2. Hardware Bill of Materials (HBOM) Generation
*   **Component Classification (VIPR-PCB, FICS-PCB)**:
    *   Standardize your classification labels. VIPR-PCB proposes a **10-class macro component digest** to parse arbitrary PCB component layouts:
        $$\text{Class List} = \{\text{Programmable IC, Non-Programmable IC, Resistor, Capacitor, Crystal, Memory, Inductor, Transistor, Diode, Connector}\}$$
*   **Datasheet Mining (WOOT17)**:
    *   Once part numbers are recognized from OCR, automate Google/Datasheet search engine queries to fetch technical PDFs.
    *   Convert PDFs to structural XML (using `pdfminer`) and check for sections like "Feature Description" or "Datasheet" to filter out marketing brochures.
*   **Pinout & Signal Extraction (WOOT17)**:
    *   Locate vector pinout diagrams in datasheets and rasterize pages to images using poppler (`pdftoppm`).
    *   Use PDF table extractors (like `Tabula`) to scrape pin-signal tables (e.g., mapping Pin 1 ➔ TX, Pin 2 ➔ RX, Pin 8 ➔ VCC) into parseable CSV files to build the HBOM database.

---

### 3. Power and Ground Rail Detection
*   **Width-based Trace Segmentation (FPIC)**:
    *   Power rails (VCC/GND) require wider traces to handle higher current. Signal lines are thin.
    *   *Clue*: Run distance transforms or edge thickness algorithms on copper mask segmentations to isolate traces exceeding signal-width limits.
*   **Silkscreen Anchor Matching (FPIC)**:
    *   Scan Board-class silkscreen text for coordinates matching `"PWR"`, `"VCC"`, or `"GND"`. Use these coordinates as spatial seed points to locate the primary power plane / rail traces.
*   **Functional Pin Connectivity (VIPR-PCB, PROBoter)**:
    *   Correlate layout pins with the extracted datasheet pinouts. Traces originating from Pins mapped to VCC/GND in the HBOM can be automatically labeled as power/ground rails.
*   **Active Voltage Probing (PROBoter)**:
    *   PROBoter automates trace verification by moving physical spring-loaded multimeter probes to identified IC pin coordinates and executing a delta voltage analysis to distinguish between power lines, clock lines, and signal lines in real-time.

---

## 📂 Public Dataset & Code Resources

To fix class imbalances (like your missing diodes, fuses, and transistors), leverage these open-source datasets:

| Dataset | Focus | Scale / Contents | Resource Link |
| :--- | :--- | :--- | :--- |
| **FPIC** | Semantic boundaries, designators, device text | 261 images, 71k instances | [TrustHub FPIC](https://www.trust-hub.org/#/data/pcb-images) |
| **FICS-PCB** | Multi-modal lighting, scale, and sensor variations | 9,912 images, 77k instances | [TrustHub FICS-PCB](https://www.trust-hub.org/data) |
| **ICText** | Character-level annotations, low-contrast/blurry/broken labels | 10,000 images, 100k characters | [ICText-AGCL GitHub](https://github.com/chunchet-ng/ICText-AGCL) |
| **PCB-GOOGLE** / **IC-PINS** | Populated PCB active components & IC pin center coordinates | 190 board images, 46 macro pin images | [PROBoter GitHub](https://github.com/schutzwerk/PROBoter) |
| **PCB-DSLR** | High-res DSLR images of IC locations and board orientations | 165 PCBs, 2,048 annotations | [MVA 2015 Archive](https://doi.org/10.1109/MVA.2015.7153209) |
