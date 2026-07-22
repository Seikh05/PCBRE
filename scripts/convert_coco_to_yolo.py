import os
import json
import shutil
import random
from pathlib import Path

def convert_coco_to_yolo(
    coco_json_path, 
    images_dir, 
    output_dir, 
    split_ratio=0.8, 
    use_obb=False
):
    """
    Converts COCO json annotations to YOLO format.
    
    Args:
        coco_json_path (str/Path): Path to labels.json
        images_dir (str/Path): Path to folder containing image files
        output_dir (str/Path): Target folder for the YOLO structured dataset
        split_ratio (float): Ratio of training images (default: 0.8)
        use_obb (bool): If True, exports in YOLO OBB format (class x1 y1 x2 y2 x3 y3 x4 y4).
                        If False, exports in standard YOLO format (class x_center y_center w h).
    """
    coco_json_path = Path(coco_json_path)
    images_dir = Path(images_dir)
    output_dir = Path(output_dir)
    
    # Load COCO JSON
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
        
    # Maps
    images_map = {img['id']: img for img in coco_data['images']}
    
    # Categories map (YOLO class ids start from 0)
    # COCO categories are often 1-indexed, map them to 0-indexed YOLO ids
    cat_ids = sorted([cat['id'] for cat in coco_data['categories']])
    cat_map = {cat_id: idx for idx, cat_id in enumerate(cat_ids)}
    
    # Store category names
    cat_names = {idx: cat['name'] for cat, idx in zip(coco_data['categories'], cat_map.values())}
    
    # Group annotations by image_id
    annotations_by_image = {}
    for ann in coco_data['annotations']:
        img_id = ann['image_id']
        if img_id not in annotations_by_image:
            annotations_by_image[img_id] = []
        annotations_by_image[img_id].append(ann)
        
    # Prepare directories
    modes = ['train', 'val']
    subdirs = ['images', 'labels']
    for mode in modes:
        for subdir in subdirs:
            (output_dir / mode / subdir).mkdir(parents=True, exist_ok=True)
            
    # List of all valid images
    all_image_ids = list(images_map.keys())
    # Shuffle for splitting
    random.seed(42)
    random.shuffle(all_image_ids)
    
    split_idx = int(len(all_image_ids) * split_ratio)
    train_ids = all_image_ids[:split_idx]
    val_ids = all_image_ids[split_idx:]
    
    dataset_splits = {
        'train': train_ids,
        'val': val_ids
    }
    
    print(f"Total images found: {len(all_image_ids)}")
    print(f"Training set: {len(train_ids)} images")
    print(f"Validation set: {len(val_ids)} images")
    
    for split_name, img_ids in dataset_splits.items():
        for img_id in img_ids:
            img_info = images_map[img_id]
            file_name = img_info['file_name']
            img_width = img_info['width']
            img_height = img_info['height']
            
            src_image_path = images_dir / file_name
            if not src_image_path.exists():
                print(f"Warning: Image file {src_image_path} does not exist. Skipping.")
                continue
                
            # Target image path
            dest_image_path = output_dir / split_name / 'images' / file_name
            shutil.copy(src_image_path, dest_image_path)
            
            # Label lines
            label_lines = []
            anns = annotations_by_image.get(img_id, [])
            
            for ann in anns:
                cat_id = ann['category_id']
                yolo_class_id = cat_map[cat_id]
                
                if use_obb:
                    # Oriented Bounding Box format using segmentation polygons
                    # YOLO OBB format needs normalized coordinates: class x1 y1 x2 y2 x3 y3 x4 y4
                    if 'segmentation' in ann and len(ann['segmentation']) > 0:
                        polygon = ann['segmentation'][0]
                        # Verify polygon has exactly 4 points (8 values)
                        if len(polygon) == 8:
                            norm_poly = []
                            for idx in range(0, 8, 2):
                                px = polygon[idx] / img_width
                                py = polygon[idx+1] / img_height
                                norm_poly.extend([px, py])
                            
                            poly_str = " ".join([f"{coord:.6f}" for coord in norm_poly])
                            label_lines.append(f"{yolo_class_id} {poly_str}")
                        else:
                            # Fallback if polygon does not have 4 vertices (e.g. segmentation is a complex shape)
                            # Convert bbox to OBB representation
                            bbox = ann['bbox']
                            x_min, y_min, w, h = bbox
                            x1, y1 = x_min, y_min
                            x2, y2 = x_min + w, y_min
                            x3, y3 = x_min + w, y_min + h
                            x4, y4 = x_min, y_min + h
                            poly_str = f"{x1/img_width:.6f} {y1/img_height:.6f} {x2/img_width:.6f} {y2/img_height:.6f} {x3/img_width:.6f} {y3/img_height:.6f} {x4/img_width:.6f} {y4/img_height:.6f}"
                            label_lines.append(f"{yolo_class_id} {poly_str}")
                else:
                    # Standard YOLO box detection format: class x_center y_center width height
                    bbox = ann['bbox'] # [x_min, y_min, width, height]
                    x_min, y_min, w, h = bbox
                    
                    x_center = x_min + w / 2.0
                    y_center = y_min + h / 2.0
                    
                    # Normalize
                    x_center_norm = x_center / img_width
                    y_center_norm = y_center / img_height
                    w_norm = w / img_width
                    h_norm = h / img_height
                    
                    label_lines.append(f"{yolo_class_id} {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}")
                    
            # Write label file
            label_file_name = Path(file_name).with_suffix('.txt')
            dest_label_path = output_dir / split_name / 'labels' / label_file_name
            with open(dest_label_path, 'w') as lf:
                lf.write("\n".join(label_lines))
                
    # Create data.yaml
    yaml_content = f"path: {output_dir.resolve().as_posix()}\n"
    yaml_content += f"train: train/images\n"
    yaml_content += f"val: val/images\n\n"
    yaml_content += f"names:\n"
    for class_id, class_name in cat_names.items():
        yaml_content += f"  {class_id}: {class_name}\n"
        
    with open(output_dir / 'data.yaml', 'w') as yf:
        yf.write(yaml_content)
        
    print(f"Dataset successfully created at {output_dir}")
    print(f"data.yaml created with paths.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert COCO JSON to YOLO format")
    parser.add_argument("--coco_json", type=str, required=True, help="Path to COCO labels.json")
    parser.add_argument("--images_dir", type=str, required=True, help="Path to image directory")
    parser.add_argument("--output_dir", type=str, required=True, help="Path to output directory")
    parser.add_argument("--split", type=float, default=0.8, help="Train/val split ratio (default 0.8)")
    parser.add_argument("--obb", action="store_true", help="Convert to YOLO Oriented Bounding Box (OBB) format")
    
    args = parser.parse_args()
    
    convert_coco_to_yolo(
        coco_json_path=args.coco_json,
        images_dir=args.images_dir,
        output_dir=args.output_dir,
        split_ratio=args.split,
        use_obb=args.obb
    )
