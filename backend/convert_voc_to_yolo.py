#!/usr/bin/env python3
"""RSOD 数据集转换工具"""

import os
import sys
from pathlib import Path
from PIL import Image

# 导入路径管理模块
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.utils.paths import Paths


def convert_voc_to_yolo(txt_path):
    """将 VOC 格式转换为 YOLO 格式"""
    yolo_lines = []

    img_path = txt_path.replace('labels', 'images').replace('.txt', '.jpg')

    if not os.path.exists(img_path):
        img_path = txt_path.replace('labels', 'images').replace('.txt', '.png')

    if not os.path.exists(img_path):
        print(f"图片不存在: {img_path}")
        return ""

    with Image.open(img_path) as img:
        img_width, img_height = img.size

    with open(txt_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue

        try:
            img_file = parts[0]
            cls_name = parts[1]
            xmin = float(parts[2])
            ymin = float(parts[3])
            xmax = float(parts[4])
            ymax = float(parts[5])

            x_center = (xmin + xmax) / 2.0 / img_width
            y_center = (ymin + ymax) / 2.0 / img_height
            bbox_width = (xmax - xmin) / img_width
            bbox_height = (ymax - ymin) / img_height

            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))
            bbox_width = max(0, min(1, bbox_width))
            bbox_height = max(0, min(1, bbox_height))

            if bbox_width > 0 and bbox_height > 0:
                yolo_lines.append(f"0 {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}")
        except (ValueError, IndexError):
            continue

    return "\n".join(yolo_lines)


def process_dataset(labels_dir):
    """处理整个标注目录"""
    txt_files = list(Path(labels_dir).glob("*.txt"))

    for txt_file in txt_files:
        yolo_content = convert_voc_to_yolo(str(txt_file))

        if yolo_content:
            with open(txt_file, 'w') as f:
                f.write(yolo_content)
            print(f"已转换: {txt_file.name}")
        else:
            print(f"跳过(无有效标注): {txt_file.name}")


if __name__ == "__main__":
    # ✅ 使用 Paths 统一管理路径
    # 优点：
    # 1. 不需要知道项目在哪个磁盘
    # 2. 不需要手动拼接路径字符串
    # 3. 所有路径集中在一处，修改方便
    rsod_dir = Paths.rsod_data()
    
    # 确保输出目录存在
    Paths.ensure_dir(rsod_dir / "train" / "labels")
    Paths.ensure_dir(rsod_dir / "test" / "labels")

    print("转换训练集标注...")
    process_dataset(rsod_dir / "train" / "labels")

    print("\n转换测试集标注...")
    process_dataset(rsod_dir / "test" / "labels")

    print("\n转换完成！")