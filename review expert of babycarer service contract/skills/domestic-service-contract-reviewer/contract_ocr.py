from paddleocr import PaddleOCR
import os
import sys

def print_usage():
    """Print usage information."""
    print("=" * 60)
    print("家政服务合同OCR提取工具")
    print("=" * 60)
    print("\n用法:")
    print("  python contract_ocr.py <image_dir> [output_file]\n")
    print("参数:")
    print("  image_dir   必需 - 合同图片所在的目录（支持绝对路径或相对路径）")
    print("  output_file 可选 - OCR结果输出文件路径，默认为当前目录的contract_ocr.txt\n")
    print("示例:")
    print("  # 使用绝对路径")
    print("  python contract_ocr.py \"C:\\project\\uploads\" \"C:\\project\\contract_ocr.txt\"")
    print("\n  # 使用相对路径（从项目根目录执行）")
    print("  python contract_ocr.py uploads contract_ocr.txt")
    print("=" * 60)

# Parse command line arguments
if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
    print_usage()
    sys.exit(0 if len(sys.argv) < 2 else 0)

image_dir = sys.argv[1]
output_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(image_dir), "contract_ocr.txt")

# Validate image directory
if not os.path.isdir(image_dir):
    raise SystemExit(f"错误：图片目录不存在: {image_dir}\n\n请使用正确的图片目录路径。")

# Validate output directory
output_dir = os.path.dirname(output_file)
if output_dir and not os.path.exists(output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        raise SystemExit(f"错误：无法创建输出目录 {output_dir}: {e}")

# Initialize PaddleOCR
model_dir_root = r"C:\paddle_models"
if os.path.exists("model_path.txt"):
    with open("model_path.txt", "r") as f:
        read_path = f.read().strip()
        if os.path.exists(read_path):
            model_dir_root = read_path

print(f"使用模型目录: {model_dir_root}")

try:
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang="ch",
        use_gpu=False,
        show_log=False,
        det_model_dir=os.path.join(model_dir_root, "det"),
        rec_model_dir=os.path.join(model_dir_root, "rec"),
        cls_model_dir=os.path.join(model_dir_root, "cls"),
    )
except Exception as e:
    raise SystemExit(f"错误：初始化OCR模型失败: {e}\n\n请检查模型目录是否正确。")

# Find all image files in the directory
image_files = []
for name in sorted(os.listdir(image_dir)):
    lower = name.lower()
    if lower.endswith((".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")):
        image_files.append(os.path.join(image_dir, name))

# Check if any images were found
if len(image_files) == 0:
    raise SystemExit(f"错误：在目录 {image_dir} 中未找到任何图片文件。\n\n支持的格式: .jpg, .jpeg, .png, .bmp, .tif, .tiff, .webp")

print(f"开始OCR处理，共找到 {len(image_files)} 张图片")
print(f"输入目录: {os.path.abspath(image_dir)}")
print(f"输出文件: {os.path.abspath(output_file)}")
print("-" * 60)

# Process each image
with open(output_file, "w", encoding="utf-8") as f:
    for idx, img_path in enumerate(image_files, 1):
        if not os.path.exists(img_path):
            print(f"警告: 文件不存在: {img_path}")
            continue

        print(f"[{idx}/{len(image_files)}] 处理中: {os.path.basename(img_path)}")
        f.write(f"==== Page: {os.path.basename(img_path)} ====\n")

        try:
            result = ocr.ocr(img_path, cls=True)
            if result and result[0]:
                for line in result[0]:
                    text = line[1][0]
                    f.write(text + "\n")
            else:
                f.write("[No text detected]\n")
        except Exception as e:
            print(f"错误: 处理失败 {os.path.basename(img_path)}: {e}")
            f.write(f"[Error processing image: {e}]\n")

        f.write("\n")

print("-" * 60)
print(f"完成! 结果已保存到: {os.path.abspath(output_file)}")
