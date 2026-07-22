import argparse
import os
import cv2
from pathlib import Path
from ultralytics import YOLO

def run_inference(model_path, image_path, output_dir, conf_threshold=0.25):
    """
    Runs YOLOv8-OBB inference on a target image to detect pins.
    
    Args:
        model_path (str): Path to the trained YOLO OBB weight file (.pt).
        image_path (str): Path to the input image file.
        output_dir (str): Folder where annotated results will be saved.
        conf_threshold (float): Confidence threshold for detections.
    """
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not image_path.exists():
        print(f"[ERROR] Input image '{image_path}' not found.")
        return
        
    import torch

    # Patch torch.load to default weights_only=False to support older ultralytics on PyTorch 2.6
    original_torch_load = torch.load
    def patched_torch_load(*args, **kwargs):
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return original_torch_load(*args, **kwargs)
    torch.load = patched_torch_load

    print(f"Loading OBB model from: {model_path}")
    model = YOLO(model_path)
    
    print(f"Running inference on: {image_path}")
    results = model.predict(source=str(image_path), conf=conf_threshold, save=False)
    
    for idx, result in enumerate(results):
        # 1. Count the number of pins detected
        obb_boxes = result.obb
        num_pins = len(obb_boxes)
        print(f"\nDetection Results for {image_path.name}:")
        print(f"------------------------------------")
        print(f"Total objects detected: {num_pins}")
        
        yolo_lines = []
        # 2. Iterate through detections and extract normalized coordinates
        if num_pins > 0:
            xyxyxyxy = obb_boxes.xyxyxyxy.cpu().numpy()
            confidences = obb_boxes.conf.cpu().numpy()
            classes = obb_boxes.cls.cpu().numpy()
            img_h, img_w = result.orig_shape
            
            print("\nYOLO Formatted OBB Results (Normalized: class_id x1 y1 x2 y2 x3 y3 x4 y4):")
            print("------------------------------------")
            for i in range(num_pins):
                corners = xyxyxyxy[i]
                conf = confidences[i]
                cls = classes[i]
                
                # Normalize corners relative to image width and height
                norm_corners = []
                for pt in corners:
                    norm_corners.append(pt[0] / img_w)
                    norm_corners.append(pt[1] / img_h)
                
                yolo_line = f"{int(cls)} " + " ".join([f"{coord:.6f}" for coord in norm_corners])
                yolo_lines.append(yolo_line)
                print(f"{yolo_line}  (conf: {conf:.3f})")
        else:
            print("  No objects detected in the image.")
            
        # 3. Save the plotted/annotated image and the YOLO labels
        annotated_img = result.plot() # returns BGR numpy array with OBB plots
        save_img_path = output_dir / f"inferred_{image_path.stem}.png"
        cv2.imwrite(str(save_img_path), annotated_img)
        
        save_txt_path = output_dir / f"inferred_{image_path.stem}.txt"
        with open(save_txt_path, 'w') as lf:
            lf.write("\n".join(yolo_lines))
            
        print(f"------------------------------------")
        print(f"Annotated result image saved to: {save_img_path.resolve()}")
        print(f"YOLO format labels saved to: {save_txt_path.resolve()}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Infer IC pins using YOLO OBB model")
    parser.add_argument("--model", type=str, default="models/ic_pin_yolo.pt", help="Path to YOLO OBB model weights")
    parser.add_argument("--image", type=str, required=True, help="Path to input image to infer")
    parser.add_argument("--out_dir", type=str, default="yolo_results", help="Directory to save output image")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold for predictions")
    
    args = parser.parse_args()
    
    run_inference(
        model_path=args.model,
        image_path=args.image,
        output_dir=args.out_dir,
        conf_threshold=args.conf
    )
