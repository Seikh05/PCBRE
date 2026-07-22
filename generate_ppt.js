const pptxgen = require("pptxgenjs");
let pptx = new pptxgen();

pptx.layout = 'LAYOUT_16x9';

// Styling helpers
const colors = {
    bg: "F8FAFC",
    title: "1F4E79",
    body: "334155",
    accentRed: "BE123C",
    accentGreen: "2E7559",
    line: "CBD5E1",
    footer: "94A3B8"
};

function addHeader(slide, titleText, slideNum) {
    // Background
    slide.background = { color: colors.bg };
    // Title
    slide.addText(titleText, { x: 0.6, y: 0.4, w: 10, h: 0.5, fontSize: 24, fontFace: "Trebuchet MS", color: colors.title, bold: true });
    // Thin horizontal rule
    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 0.95, w: 12.13, h: 0.03, fill: { color: colors.line } });
    // Footer
    slide.addText("PCBRE: Multi-Modal Hardware Auditing | IISc DESE", { x: 0.6, y: 7.1, w: 8, h: 0.3, fontSize: 10, fontFace: "Calibri", color: colors.footer });
    slide.addText("Slide " + slideNum + " / 12", { x: 11.0, y: 7.1, w: 1.7, h: 0.3, fontSize: 10, fontFace: "Calibri", color: colors.footer, align: "right" });
}

// ==========================================
// SLIDE 1: TITLE SLIDE
// ==========================================
let s1 = pptx.addSlide();
s1.background = { color: "FFFFFF" };
s1.addShape(pptx.shapes.RECTANGLE, { x: 0.0, y: 0.0, w: 0.4, h: 7.5, fill: { color: colors.title } });
s1.addText("PCBRE: A Multi-Modal Hardware Auditing & Reverse Engineering Framework", {
    x: 0.8, y: 1.8, w: 11.5, h: 1.5,
    fontSize: 32, fontFace: "Trebuchet MS", color: colors.title, bold: true
});
s1.addText("Non-Destructive Supply Chain Security and PCB Assurance via Deep Learning & LMMs", {
    x: 0.8, y: 3.4, w: 11.5, h: 0.8,
    fontSize: 18, fontFace: "Calibri", color: "475569", italic: true
});
s1.addShape(pptx.shapes.RECTANGLE, { x: 0.8, y: 4.4, w: 4.0, h: 0.04, fill: { color: "10B981" } });
s1.addText("Candidate: Seikh Souvagya Mustakim (B.Tech ETC)\nGuide: Dr. Haresh Dagale (DESE, IISc Bengaluru)\nProgram: IASc-INSA-NASI Summer Research Fellowship Programme (2026)", {
    x: 0.8, y: 4.8, w: 11.0, h: 1.5,
    fontSize: 12, fontFace: "Calibri", color: "334155"
});

// ==========================================
// SLIDE 2: BACKGROUND & MOTIVATION
// ==========================================
let s2 = pptx.addSlide();
addHeader(s2, "1. Background & Supply Chain Vulnerabilities", "2");
s2.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F1F5F9" }, line: { color: "CBD5E1", width: 1 } });
s2.addText("THE HARDWARE SECURITY IMPERATIVE", { x: 0.9, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.accentRed, bold: true });
s2.addText("• Supply Chain Security:\n  Globalized semiconductor manufacturing introduces serious security boundaries. Hardware Trojans or counterfeit chip substitutions can be introduced before final system assembly.\n\n• The Need for RE:\n  Hardware reverse engineering acts as the final audit line to verify physical layout integrity against design specifications.", {
    x: 0.9, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

s2.addShape(pptx.shapes.RECTANGLE, { x: 6.8, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F1F5F9" }, line: { color: "CBD5E1", width: 1 } });
s2.addText("LIMITATIONS OF THE STATE-OF-THE-ART", { x: 7.1, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.title, bold: true });
s2.addText("• Chemical De-layering:\n  Highly destructive, uses hazardous acids (nitric/hydrofluoric), and destroys active boards permanently.\n\n• Contact-Based Probing (PROBoter):\n  Requires millimetre-precision robotic calibration, and risks trace-level mechanical damage.\n\n• CAD dependency (VIPR-PCB):\n  Strict dependency on KiCAD or Altium netlists, which are unavailable for black-box audits.", {
    x: 7.1, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

// ==========================================
// SLIDE 3: modular PIPELINE ARCHITECTURE
// ==========================================
let s3 = pptx.addSlide();
addHeader(s3, "2. Modular Pipeline Architecture", "3");
s3.addText("TRADITIONAL BASELINE", { x: 0.6, y: 1.3, w: 5.8, h: 0.3, fontSize: 14, fontFace: "Trebuchet MS", color: "64748B", bold: true, align: "center" });
s3.addText("PROPOSED PCBRE PIPELINE (OURS)", { x: 6.8, y: 1.3, w: 5.8, h: 0.3, fontSize: 14, fontFace: "Trebuchet MS", color: colors.title, bold: true, align: "center" });

s3.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 1.5, y: 1.8, w: 4.0, h: 1.0, fill: { color: "E2E8F0" }, line: { color: "CBD5E1" } });
s3.addText("Stage 1: HSV Masking\n(Component Detection)", { x: 1.5, y: 1.8, w: 4.0, h: 1.0, fontSize: 11, color: "475569", align: "center", vertical: "middle", bold: true });
s3.addText("↓", { x: 1.5, y: 2.9, w: 4.0, h: 0.3, fontSize: 14, color: "64748B", align: "center" });
s3.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 1.5, y: 3.3, w: 4.0, h: 1.0, fill: { color: "E2E8F0" }, line: { color: "CBD5E1" } });
s3.addText("Stage 2: CLAHE + Sharp\n(OCR Preprocessing)", { x: 1.5, y: 3.3, w: 4.0, h: 1.0, fontSize: 11, color: "475569", align: "center", vertical: "middle", bold: true });

s3.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 7.7, y: 1.8, w: 4.0, h: 1.0, fill: { color: "1F4E79" }, line: { color: "0F172A" } });
s3.addText("Stage 3: YOLOv8m-OBB\n(Component Detection)", { x: 7.7, y: 1.8, w: 4.0, h: 1.0, fontSize: 11, color: "FFFFFF", align: "center", vertical: "middle", bold: true });
s3.addText("↓", { x: 7.7, y: 2.9, w: 4.0, h: 0.3, fontSize: 14, color: "1F4E79", align: "center" });
s3.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 7.7, y: 3.3, w: 4.0, h: 1.0, fill: { color: "2E7559" }, line: { color: "14532D" } });
s3.addText("Gemini 1.5 Flash LMM\n(OCR / Text Extraction)", { x: 7.7, y: 3.3, w: 4.0, h: 1.0, fontSize: 11, color: "FFFFFF", align: "center", vertical: "middle", bold: true });
s3.addText("↓", { x: 7.7, y: 4.4, w: 4.0, h: 0.3, fontSize: 14, color: "1F4E79", align: "center" });
s3.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 7.7, y: 4.8, w: 4.0, h: 1.0, fill: { color: "1F4E79" }, line: { color: "0F172A" } });
s3.addText("Stage 4: Power Net Mapper\n(Topology Mapping)", { x: 7.7, y: 4.8, w: 4.0, h: 1.0, fontSize: 11, color: "FFFFFF", align: "center", vertical: "middle", bold: true });

s3.addText("Key Operational Division of Labor:\n• Traditional Preprocessing uses color thresholding which is fragile, and document-level OCR which fails on rotated board structures.\n• Proposed Pipeline separates concerns: Stage 3 handles orientation-invariant component detection, cloud LMM solves OCR under noise, and Stage 4 handles visual width heuristics.", {
    x: 0.6, y: 5.9, w: 12.1, h: 1.0, fontSize: 11, fontFace: "Calibri", color: colors.body
});

// ==========================================
// SLIDE 4: STAGE 1 SUBSTRATE & HEURISTIC LIMITS
// ==========================================
let s4 = pptx.addSlide();
addHeader(s4, "3. Stage 1: Substrate Segmentation & Heuristic Limits", "4");

s4.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F8FAFC" }, line: { color: "E2E8F0" } });
s4.addText("HSV MORPHOLOGICAL SEGMENTATION", { x: 0.9, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.title, bold: true });
s4.addText("• Principle:\n  Converts BGR to Hue-Saturation-Value (HSV) space to isolate background resin (green, blue, black) from foreground copper pads and IC bodies.\n\n• Decoupled Luminance:\n  V channel isolates lighting variance while H and S channels track dye color boundaries.\n\n• Math Formulation:\n  Mask M(x,y) = 1 if H, S, V fall within defined bounds; 0 otherwise.", {
    x: 0.9, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

s4.addShape(pptx.shapes.RECTANGLE, { x: 6.8, y: 1.3, w: 5.8, h: 5.4, fill: { color: "FFF1F2" }, line: { color: "FECDD3" } });
s4.addText("WHY CLASSICAL SEGMENTATION FAILS", { x: 7.1, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: "9F1239", bold: true });
s4.addText("• Manual Calibration Vulnerability:\n  Different solder mask formulations vary green values by up to ±15 hue units. Red and black boards require manual recalibration of range sliders.\n\n• Lighting & Specular Fragility:\n  Reflective solder joints create specular highlights that mimic IC packages. Minor lighting changes break previously tuned parameters.\n\n• No Semantics:\n  Only yields binary shapes. Cannot distinguish an IC from a capacitor or heatsink, necessitating deep learning.", {
    x: 7.1, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: "475569"
});

// ==========================================
// SLIDE 5: STAGE 2 IMAGE SHARPENING
// ==========================================
let s5 = pptx.addSlide();
addHeader(s5, "4. Stage 2: OCR Preprocessing & Sharpening Math", "5");
s5.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 12.1, h: 5.4, fill: { color: "F8FAFC" }, line: { color: "E2E8F0" } });
s5.addText("GAUSSIAN UNSHARP MASKING & CLAHE", { x: 1.0, y: 1.6, w: 11.3, h: 0.4, fontSize: 16, fontFace: "Trebuchet MS", color: colors.title, bold: true });
s5.addText("To enhance degraded, laser-etched alphanumeric package markings under uneven lighting, we use a hybrid pipeline:", {
    x: 1.0, y: 2.1, w: 11.3, h: 0.5, fontSize: 14, fontFace: "Calibri", color: colors.body
});

s5.addShape(pptx.shapes.RECTANGLE, { x: 1.0, y: 2.8, w: 5.3, h: 3.4, fill: { color: "FFFFFF" }, line: { color: "E2E8F0" } });
s5.addText("Contrast Limited AHE (CLAHE)\n\n• Operates locally on small image tiles (8x8 pixels).\n• Limits histogram amplification to clip noise amplification in flat chip packages.\n• Restores contrast uniformly across laser-etched markings.", {
    x: 1.2, y: 3.0, w: 4.9, h: 3.0, fontSize: 11, fontFace: "Calibri", color: colors.body
});

s5.addShape(pptx.shapes.RECTANGLE, { x: 6.8, y: 2.8, w: 5.5, h: 3.4, fill: { color: "FFFFFF" }, line: { color: "E2E8F0" } });
s5.addText("Gaussian Unsharp Masking\n\n• Generates edge mask by subtracting blurred image:\n  g_mask(x,y) = f(x,y) - G_σ(x,y) * f(x,y)\n• Re-adds scaled mask to restore high frequency details:\n  g(x,y) = f(x,y) + α · g_mask(x,y)\n• Setting σ = 1.0 and α ∈ [1.0, 2.0] sharpens character edges.", {
    x: 7.0, y: 3.0, w: 5.1, h: 3.0, fontSize: 11, fontFace: "Calibri", color: colors.body
});

// ==========================================
// SLIDE 6: STAGE 3 YOLO OBB CORE
// ==========================================
let s6 = pptx.addSlide();
addHeader(s6, "5. Stage 3: YOLOv8m-OBB Component Localization", "6");

s6.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F8FAFC" }, line: { color: "E2E8F0" } });
s6.addText("WHY ORIENTED BOUNDING BOXES?", { x: 0.9, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.title, bold: true });
s6.addText("• Horizontal Bounding Box (HBB) limits:\n  When components are rotated (e.g., at 45° or 30°), HBB bounding boxes overlap, merging adjacent pins and creating severe localization errors.\n\n• Oriented Bounding Box (OBB):\n  Adds a 5th degree of freedom—rotation angle θ:\n  b = {x_c, y_c, w, h, θ}\n\n• Benefits:\n  Rotation-invariant component detection and separation of closely packed passive elements.", {
    x: 0.9, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

s6.addShape(pptx.shapes.RECTANGLE, { x: 6.8, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F8FAFC" }, line: { color: "E2E8F0" } });
s6.addText("TRAINING CONFIGURATION", { x: 7.1, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.accentGreen, bold: true });
s6.addText("• Model Architectures:\n  Evaluated YOLOv8-OBB configurations (Nano, Small, Medium) to establish throughput/accuracy tradeoffs.\n\n• Image Resolution (1024x1024):\n  Increasing training resolution from 640 to 1024 was critical to preserve the visual features of sub-millimeter passive elements (0402 resistors, caps) in macro photos.\n\n• Parameter Count:\n  YOLOv8m-OBB trains 26.4M parameters to achieve optimal balance.", {
    x: 7.1, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

// ==========================================
// SLIDE 7: YOLO OBB PERFORMANCE & DIAGNOSTICS
// ==========================================
let s7 = pptx.addSlide();
addHeader(s7, "6. YOLOv8-OBB Results & Error Analysis", "7");

s7.addText("MODEL VALIDATION RESULTS (mAP@0.5)", { x: 0.6, y: 1.3, w: 6.2, h: 0.3, fontSize: 12, fontFace: "Trebuchet MS", color: colors.title, bold: true });

let valRows = [
    ["Class", "Instances", "YOLOv8n", "YOLOv8s", "YOLOv8m"],
    ["All Classes", "979", "0.445", "0.569", "0.749"],
    ["ICs", "45", "0.772", "0.850", "0.732"],
    ["Capacitors", "508", "0.553", "0.721", "0.785"],
    ["Resistors", "401", "0.127", "0.414", "0.581"]
];

s7.addTable(valRows, {
    x: 0.6, y: 1.7, w: 6.2, h: 2.2,
    border: { type: "solid", color: "CBD5E1", pt: 1 },
    fill: "FFFFFF",
    fontSize: 11,
    fontFace: "Calibri",
    align: "center",
    colW: [1.8, 1.0, 1.1, 1.1, 1.2]
});

s7.addText("Key finding: YOLOv8m-OBB shows 30.4% mAP improvement over baseline due to capacity and resolution expansion.", {
    x: 0.6, y: 4.1, w: 6.2, h: 2.4, fontSize: 11, fontFace: "Calibri", color: colors.body, italic: true
});

s7.addShape(pptx.shapes.RECTANGLE, { x: 7.0, y: 1.3, w: 5.7, h: 5.4, fill: { color: "FFF1F2" }, line: { color: "FECDD3" } });
s7.addText("EXPERIMENTAL ERROR DIAGNOSTICS", { x: 7.3, y: 1.5, w: 5.1, h: 0.4, fontSize: 13, fontFace: "Trebuchet MS", color: "9F1239", bold: true });
s7.addText("• Diode Anomaly:\n  Only 1 diode in validation set. Extreme statistical variance (mAP 0.000 in Small vs. 0.995 in Medium).\n\n• Transistor Loss Dominance:\n  Only 6 transistors present. Gradients dominated by dominant Resistor/Capacitor targets, limiting mAP.\n\n• Resistor Downsampling Loss:\n  Tiny 0402 package shapes (3x6px) lose spatial features in deep neural layers, causing them to merge with neighboring pads.", {
    x: 7.3, y: 2.0, w: 5.1, h: 4.3, fontSize: 11, fontFace: "Calibri", color: "475569"
});

// ==========================================
// SLIDE 8: OCR DOMAIN SHIFT
// ==========================================
let s8 = pptx.addSlide();
addHeader(s8, "7. OCR Domain Shift: Local vs. LMM Attention", "8");

s8.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F8FAFC" }, line: { color: "E2E8F0" } });
s8.addText("LOCAL OCR LIMITATIONS", { x: 0.9, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.accentRed, bold: true });
s8.addText("• Suffix Truncation:\n  Local engines (PaddleOCR, EasyOCR) lack semantic understanding. They read text literally, truncating crucial suffixes:\n  ❌ 'STM32F745VGT6' → read as 'STM32F745'\n\n• Background Noise:\n  Polished mold compounds and laser etching create reflections that local binarization algorithms classify as letters, corrupting results.", {
    x: 0.9, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

s8.addShape(pptx.shapes.RECTANGLE, { x: 6.8, y: 1.3, w: 5.8, h: 5.4, fill: { color: "ECFDF5" }, line: { color: "A7F3D0" } });
s8.addText("PROPOSED LMM ATTENTION (GEMINI FLASH)", { x: 7.1, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: "065F46", bold: true });
s8.addText("• Contextual Error Correction:\n  LMMs combine visual OCR with massive semantic knowledge of chip naming conventions.\n  ✅ 'STM32F745VGT6' is read correctly.\n\n• Rotation Tolerance:\n  Zero-shot Gemini 1.5 Flash processes text rotated at arbitrary angles without needing orientation normalization.\n\n• HBoM Extraction:\n  Extracts part number, manufacturer, and pin count into a structured JSON record.", {
    x: 7.1, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

// ==========================================
// SLIDE 9: STAGE 4 POWER RAIL MAPPING
// ==========================================
let s9 = pptx.addSlide();
addHeader(s9, "8. Stage 4: Probe-Free Power Rail Identification", "9");

s9.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F8FAFC" }, line: { color: "E2E8F0" } });
s9.addText("DISTANCE TRANSFORM MATH", { x: 0.9, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.title, bold: true });
s9.addText("• Euclidean Distance Transform (EDT):\n  Computes distance to nearest background boundary for every foreground trace pixel:\n  D(p) = min_{q ∈ B^c} ||p - q||\n\n• Trace Width Extraction:\n  Calculated at trace centerlines via:\n  Width = 2 · max_p D(p)\n\n• Efficiency:\n  Enables fast, non-destructive trace thickness profiling across the entire board.", {
    x: 0.9, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

s9.addShape(pptx.shapes.RECTANGLE, { x: 6.8, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F8FAFC" }, line: { color: "E2E8F0" } });
s9.addText("POWER NET CLASSIFICATION", { x: 7.1, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.accentGreen, bold: true });
s9.addText("• IPC-2221 Design Standard:\n  Power nets (VCC/GND) carry higher current and are designed wider than signal lines.\n\n• Width Threshold (6.0px):\n  Traces thicker than 6.0px in macro photos are flagged as candidate power buses.\n\n• Silkscreen Mapping:\n  Gemini reads local silkscreen text nodes (e.g. 'GND', '5V', '3V3') and links them directly to the associated copper nets to map rails.", {
    x: 7.1, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

// ==========================================
// SLIDE 10: RESOLVED SOFTWARE BOTTLENECKS
// ==========================================
let s10 = pptx.addSlide();
addHeader(s10, "9. Resolved Engineering Bottlenecks", "10");
s10.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 12.1, h: 5.4, fill: { color: "FFFBEB" }, line: { color: "FDE68A" } });
s10.addText("ENGINEERING DIAGNOSTICS & BUG RESOLUTIONS", { x: 1.0, y: 1.6, w: 11.3, h: 0.4, fontSize: 16, fontFace: "Trebuchet MS", color: "92400E", bold: true });

s10.addText("1. PaddleOCR C++ Compiles (Windows OS)\n• Bug: PaddleOCR crashed local thread pools on windows due to MKLDNN library compilation errors.\n• Resolution: Forced CPU execution in app.py via app configurations ('use_mkldnn=False').", {
    x: 1.0, y: 2.2, w: 11.3, h: 1.3, fontSize: 11, fontFace: "Calibri", color: "78350F"
});

s10.addText("2. Gemini API Rate Limiting (TPM 429)\n• Bug: Sending uncompressed raw macro photos triggered 429 Token Rate Limit errors instantly.\n• Resolution: Programmed YOLO crop exporter to resize IC packages to 250px and batch queries in chunks of 3.", {
    x: 1.0, y: 3.6, w: 11.3, h: 1.3, fontSize: 11, fontFace: "Calibri", color: "78350F"
});

s10.addText("3. Flask-Jinja2 JSON Brackets Conflict\n• Bug: Jinja2 parser threw template syntax errors because Flask templating conflicted with JSON HBoM bracket notation.\n• Resolution: Structured data output schemas through raw escaping blocks.", {
    x: 1.0, y: 5.0, w: 11.3, h: 1.3, fontSize: 11, fontFace: "Calibri", color: "78350F"
});

// ==========================================
// SLIDE 11: WEB DASHBOARD
// ==========================================
let s11 = pptx.addSlide();
addHeader(s11, "10. Interactive Web Dashboard Prototype", "11");

s11.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F8FAFC" }, line: { color: "E2E8F0" } });
s11.addText("DASHBOARD CAPABILITIES", { x: 0.9, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.title, bold: true });
s11.addText("• Python-Flask Backend:\n  Integrates HSV Masking, CLAHE, YOLOv8 OBB, and Gemini API calls into a unified web runtime.\n\n• Interactive HTML5 Canvas:\n  Allows users to overlay OBB prediction boxes directly on the PCB image and edit annotations.\n\n• Live Slider Controls:\n  Real-time HSV range adjustment, CLAHE clip-limit tuning, and sharpening parameter changes.", {
    x: 0.9, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

s11.addShape(pptx.shapes.RECTANGLE, { x: 6.8, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F8FAFC" }, line: { color: "E2E8F0" } });
s11.addText("HBOM SPREADSHEET & POWER OVERLAYS", { x: 7.1, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.accentGreen, bold: true });
s11.addText("• Interactive HBoM Spreadsheet:\n  Generates editable database tables for part numbers, manufacturers, pin counts, and package types.\n\n• Export Configurations:\n  Supports instant export to JSON schema and standard CSV for external CAD matching.\n\n• Power Net Visualization:\n  Interactive SVG overlay renders glowing colored traces representing VCC (red) and GND (blue) nets.", {
    x: 7.1, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

// ==========================================
// SLIDE 12: STATUS & FUTURE ROADMAP
// ==========================================
let s12 = pptx.addSlide();
addHeader(s12, "11. Project Status & Future Technical Roadmap", "12");

s12.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 5.8, h: 5.4, fill: { color: "ECFDF5" }, line: { color: "A7F3D0" } });
s12.addText("COMPLETED MILESTONES (90%)", { x: 0.9, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: "065F46", bold: true });
s12.addText("• Classical Preprocessing Tuners:\n  Substrate HSV segmenters and image contrast/sharpening filters complete.\n\n• Oriented Detection Core:\n  YOLOv8m-OBB model successfully trained at 1024 resolution to 0.749 mAP.\n\n• LMM HBoM Parser:\n  Gemini integration handles suffix details with zero-shot rate-safe batching.\n\n• Power Net Mapper:\n  EDT trace width metrics and silkscreen matcher fully operational.", {
    x: 0.9, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

s12.addShape(pptx.shapes.RECTANGLE, { x: 6.8, y: 1.3, w: 5.8, h: 5.4, fill: { color: "F8FAFC" }, line: { color: "E2E8F0" } });
s12.addText("FUTURE WORK & ROADMAP (10%)", { x: 7.1, y: 1.5, w: 5.2, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: colors.title, bold: true });
s12.addText("• Edge Deployment (Quantization):\n  Export YOLO model weights to quantized ONNX format to enable secure, offline execution in the field on Raspberry Pi/NVIDIA Jetson.\n\n• Schematic Reconstruction:\n  Integrate skeletonization/thinning algorithms (e.g. Zhang-Suen) to extract trace centerlines and output native Altium/KiCAD schematics (.SCH).", {
    x: 7.1, y: 2.0, w: 5.2, h: 4.3, fontSize: 11, fontFace: "Calibri", color: colors.body
});

// Save presentation
pptx.writeFile({ fileName: "PCBRE_Internship_Presentation.pptx" })
    .then(fileName => {
        console.log(`Created file successfully: ${fileName}`);
    })
    .catch(err => {
        console.error("Error writing file:", err);
    });
