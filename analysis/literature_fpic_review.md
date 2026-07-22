# Literature Review: FPIC Paper Analysis
**Paper**: *FPIC: A Novel Semantic Dataset for Optical PCB Assurance* (University of Florida, FICS Research)  
**Objective**: Extract methodology clues for IC OCR, Power/Ground rail detection, and general HBOM generation.

---

## 🔍 Part 1: Clues for IC OCR (Optical Character Recognition)

The paper outlines several unique metadata attributes and challenges related to character recognition on IC packages:

1. **Text Class Separation ("Board" vs. "Device")**:
   * The paper categorizes PCB text into two classes: text printed on the substrate (**Board** silkscreen) and text laser-etched/printed on the components (**Device** text).
   * *Clue*: For IC OCR, you must first isolate the **Device** text boundaries using your object detection coordinates to avoid contamination from surrounding board designators (like "R102", "C56").
2. **Orientation Correction ($0\text{-}359^\circ$)**:
   * Text on ICs can be oriented at any angle. The paper records a specific `Orientation` angle parameter ($0$ to $359$ degrees) for text boxes.
   * *Clue*: Standard OCR engines (like EasyOCR) assume horizontal text. You must compute the dominant orientation angle of the text block/IC and **rotate the cropped IC sub-image** to a horizontal position ($0^\circ$) before feed-forwarding it to the OCR engine.
3. **Logo vs. Text Segmentation**:
   * IC surfaces contain both text (part numbers, date codes) and manufacturer logos (e.g., Texas Instruments, Analog Devices). Standard OCR engines fail when trying to read logos as text.
   * *Clue*: You need a secondary classifier or template-matching heuristic to identify and crop out logos (or ignore them) so they do not contaminate the character recognition string.

---

## ⚡ Part 2: Clues for Power and Ground Rail Detection

Section 5.3 (*Schematic analysis from component locator association*) and Figure 7 provide valuable insights on how to map trace connectivity optically:

1. **Trace Width Heuristics**:
   * Power and ground lines (VCC/GND) carry higher current than standard high-impedance signal traces. Consequently, **power traces are designed to be significantly wider** than signal traces.
   * *Clue*: You can apply morphological operations (like distance transforms or skeletonization) to segment copper traces. Traces that exceed a certain thickness threshold can be programmatically flagged as potential power/ground rails.
2. **Silkscreen Anchors (Substrate OCR)**:
   * Board-level text such as `"PWR"`, `"GND"`, `"VCC"`, or test point labels (e.g., `"TP1"`) are often printed directly on the substrate.
   * *Clue*: Run OCR on the **Board** text class. If you detect coordinate coordinates for `"GND"` or `"VCC"` text, these coordinates act as **spatial seed points**. Any wide copper trace intersecting these label boundaries is highly likely to be that specific rail.
3. **HBOM-Driven Pinout Mapping (Semantics-to-Layout)**:
   * By combining your IC OCR outputs with datasheet lookup APIs, you obtain the IC's pin configuration (e.g., Pin 8 is VCC, Pin 4 is GND).
   * *Clue*: Once the OBB detector locates the IC and identifies its orientation marker (e.g., pin 1 dot/triangle), you map the physical coordinate of the VCC/GND pins. The copper traces originating from these pins are verified as the respective power/ground rails.

---

## 📈 Part 3: How This Paper Helps Your Project

1. **Dataset Expansion (Solving Imbalance)**:
   * The paper introduces the **FPIC dataset**, which contains 261 images of 93 unique PCBs with over 71,000 annotated instances.
   * *Utility*: You can download this dataset from TrustHub (`https://www.trust-hub.org/#/data/pcb-images`) to get additional training images for your rare classes (like diodes and transistors) to solve your model imbalance.
2. **Identifying Edge-Case Pitfalls**:
   * Table 4 and Table 5 list common challenges that degrade optical performance, such as:
     * **Conformal Coating Specular Reflection**: Recommends using a polarized filter on the camera to reduce sheen.
     * **Mismatched Silkscreen vs. Component**: Highlights cases where designer silkscreen errors mismatch the actual mounted component.
     * **Run-on Designators**: Text blocks placed too closely where spaces cannot be used as separators, which can guide your localized Stage 2 OCR tuner.
