import shutil
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
src_best = os.path.join(base_dir, "runs", "detect", "rsod_yolo11n19", "weights", "best.pt")
src_last = os.path.join(base_dir, "runs", "detect", "rsod_yolo11n19", "weights", "last.pt")
target_best = os.path.join(base_dir, "runs", "detect", "best_model.pt")
target_last = os.path.join(base_dir, "runs", "detect", "last_model.pt")

shutil.copy2(src_best, target_best)
shutil.copy2(src_last, target_last)
print("✅ 模型已复制到固定位置！")
print(f"   best_model.pt -> {target_best}")
print(f"   last_model.pt -> {target_last}")
