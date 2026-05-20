import torch
import ultralytics

print(f"PyTorch版本: {torch.__version__}")
print(f"CUDA是否可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU型号: {torch.cuda.get_device_name(0)}")
    print(f"CUDA版本: {torch.version.cuda}")
    print(f"显存大小: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

print(f"\nUltralytics版本: {ultralytics.__version__}")
# 测试YOLO11推理
model = ultralytics.YOLO("yolov11n.pt")
results = model("https://ultralytics.com/images/bus.jpg")
print("\nYOLO11推理测试成功！")