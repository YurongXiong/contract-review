import os
import shutil

def fix_paddle_paths():
    print("Fixing PaddleOCR model paths...")
    
    # Source: Current location (in your user profile)
    user_home = os.path.expanduser("~")
    # Note: PaddleOCR default download path structure
    source_root = os.path.join(user_home, ".paddleocr", "whl")
    
    # Destination: A clean ASCII path (C:\paddle_models)
    # Using a folder in Public Users if C root is protected, or try C root first
    dest_root = r"C:\paddle_models"
    
    print(f"Source root: {source_root}")
    print(f"Target root: {dest_root}")
    
    # Define the specific model paths to copy
    # Based on the log output, we can see the exact folders
    models_to_move = [
        # Detection model
        (os.path.join("det", "ch", "ch_PP-OCRv4_det_infer"), "det"),
        # Recognition model
        (os.path.join("rec", "ch", "ch_PP-OCRv4_rec_infer"), "rec"),
        # Classification model
        (os.path.join("cls", "ch_ppocr_mobile_v2.0_cls_infer"), "cls")
    ]
    
    # Create destination directory
    if not os.path.exists(dest_root):
        try:
            os.makedirs(dest_root)
            print(f"Created directory: {dest_root}")
        except PermissionError:
            print(f"Error: Permission denied creating {dest_root}.")
            print("Trying C:\\Users\\Public\\paddle_models instead...")
            dest_root = r"C:\Users\Public\paddle_models"
            os.makedirs(dest_root, exist_ok=True)

    # Copy files
    for src_sub, dst_name in models_to_move:
        src_path = os.path.join(source_root, src_sub)
        dst_path = os.path.join(dest_root, dst_name)
        
        print(f"\nChecking model: {dst_name}")
        
        if not os.path.exists(src_path):
            print(f"  [Warning] Source model not found at {src_path}")
            print("  (This might happen if previous download failed. Run OCR script again to re-download if needed)")
            continue
            
        if os.path.exists(dst_path):
            print(f"  Target {dst_path} already exists. Skipping copy.")
        else:
            print(f"  Copying from {src_path} to {dst_path}...")
            try:
                shutil.copytree(src_path, dst_path)
                print("  Success!")
            except Exception as e:
                print(f"  [Error] Failed to copy: {e}")

    print(f"\nDone! Models are ready in {dest_root}")
    
    # Create a marker file so the batch script knows where we put them
    with open("model_path.txt", "w") as f:
        f.write(dest_root)

if __name__ == "__main__":
    fix_paddle_paths()
