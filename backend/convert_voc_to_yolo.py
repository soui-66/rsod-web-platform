#!/usr/bin/env python3
import os
import glob
from PIL import Image


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
    txt_files = glob.glob(os.path.join(labels_dir, "*.txt"))

    for txt_file in txt_files:
        yolo_content = convert_voc_to_yolo(txt_file)

        if yolo_content:
            with open(txt_file, 'w') as f:
                f.write(yolo_content)
            print(f"已转换: {os.path.basename(txt_file)}")
        else:
            print(f"跳过(无有效标注): {os.path.basename(txt_file)}")


if __name__ == "__main__":
    base_dir = r"D:\Users\ZFF\PycharmProjects\rsod-web-platform\backend\datasets\rsod\aircraft"

    print("转换训练集标注...")
    process_dataset(os.path.join(base_dir, "train", "labels"))

    print("\n转换测试集标注...")
    process_dataset(os.path.join(base_dir, "test", "labels"))

    print("\n转换完成！")
