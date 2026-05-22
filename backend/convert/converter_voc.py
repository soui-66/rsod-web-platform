#!/usr/bin/env python3
"""
VOC格式转YOLO格式转换器
"""

import sys
import shutil
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Dict
from PIL import Image

# 添加 backend 目录到 sys.path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.utils.logger import get_logger
logger = get_logger("converter")

from validator import quick_validate


class VOCToYOLOConverter:
    """VOC转YOLO转换器"""

    def __init__(self, dataset_info, output_dir: Path, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        self.dataset_info = dataset_info
        self.output_dir = Path(output_dir)
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio

        # 类别到ID的映射
        self.class_map = {name: idx for idx, name in enumerate(dataset_info.classes)}

    def convert(self) -> Dict[str, Path]:
        """
        执行转换

        返回：
            Dict: 各集合的目录路径
        """
        print(f"\n🔄 开始转换: {self.dataset_info.name}")

        # 创建输出目录
        splits = ['train', 'val', 'test']
        split_dirs = {}
        for split in splits:
            img_dir = self.output_dir / split / 'images'
            lbl_dir = self.output_dir / split / 'labels'
            img_dir.mkdir(parents=True, exist_ok=True)
            lbl_dir.mkdir(parents=True, exist_ok=True)
            split_dirs[split] = {'images': img_dir, 'labels': lbl_dir}

        # 获取所有有效样本
        samples = self._get_valid_samples()
        print(f"   找到 {len(samples)} 个有效样本")

        # 划分数据集
        train_samples, val_samples, test_samples = self._split_dataset(samples)
        print(f"   训练集: {len(train_samples)} | 验证集: {len(val_samples)} | 测试集: {len(test_samples)}")

        # 转换各集合
        self._convert_split(train_samples, split_dirs['train'])
        self._convert_split(val_samples, split_dirs['val'])
        self._convert_split(test_samples, split_dirs['test'])

        print(f"   ✅ 转换完成: {self.output_dir}")
        return split_dirs

    def _get_valid_samples(self) -> List[Dict]:
        """获取所有有效样本（有对应图片和标注的）"""
        samples = []

        for xml_file in self.dataset_info.labels_dir.glob('*.xml'):
            img_name = xml_file.stem

            # 查找对应的图片
            img_path = None
            for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                possible_img = self.dataset_info.images_dir / (img_name + ext)
                if possible_img.exists():
                    img_path = possible_img
                    break

            if img_path:
                samples.append({
                    'name': img_name,
                    'xml_file': xml_file,
                    'img_path': img_path
                })

        return samples

    def _split_dataset(self, samples: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """划分数据集"""
        random.shuffle(samples)

        n_total = len(samples)
        n_train = int(n_total * self.train_ratio)
        n_val = int(n_total * self.val_ratio)

        train_samples = samples[:n_train]
        val_samples = samples[n_train:n_train + n_val]
        test_samples = samples[n_train + n_val:]

        return train_samples, val_samples, test_samples

    def _convert_split(self, samples: List[Dict], split_dir: Dict):
        """转换单个数据集划分"""
        for sample in samples:
            # 复制图片
            src_img = sample['img_path']
            dst_img = split_dir['images'] / src_img.name
            shutil.copy2(src_img, dst_img)

            # 转换标注
            yolo_annotations = self._parse_voc_xml(sample['xml_file'], dst_img)

            # 保存YOLO格式标注
            dst_label = split_dir['labels'] / (sample['name'] + '.txt')
            with open(dst_label, 'w', encoding='utf-8') as f:
                f.write('\n'.join(yolo_annotations))

    def _parse_voc_xml(self, xml_file: Path, img_path: Path) -> List[str]:
        """
        解析VOC XML文件，转换为YOLO格式

        YOLO格式: class_id x_center y_center width height (均为0-1之间的归一化值)
        """
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # 获取图片尺寸
        with Image.open(img_path) as img:
            img_width, img_height = img.size

        yolo_lines = []

        for obj in root.findall('object'):
            class_name = obj.find('name').text
            if class_name not in self.class_map:
                continue

            class_id = self.class_map[class_name]

            # 获取边界框
            bbox = obj.find('bndbox')
            xmin = float(bbox.find('xmin').text)
            ymin = float(bbox.find('ymin').text)
            xmax = float(bbox.find('xmax').text)
            ymax = float(bbox.find('ymax').text)

            # 转换为YOLO格式（归一化中心坐标和宽高）
            x_center = (xmin + xmax) / 2.0 / img_width
            y_center = (ymin + ymax) / 2.0 / img_height
            width = (xmax - xmin) / img_width
            height = (ymax - ymin) / img_height

            # 确保值在0-1之间
            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))
            width = max(0, min(1, width))
            height = max(0, min(1, height))

            yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

        return yolo_lines


def convert_voc_dataset(dataset_info, converted_dir: Path) -> Dict:
    """
    转换VOC数据集为YOLO格式

    参数：
        dataset_info: 数据集信息
        converted_dir: 转换后数据存放目录

    返回：
        Dict: 包含类别信息和各集合路径
    """
    # 转换前验证
    logger.info("转换前验证...")
    if not quick_validate(dataset_info.labels_dir, dataset_info.images_dir):
        logger.error("验证失败，无法转换")
        return None
    # 创建数据集特定的输出目录
    dataset_output = converted_dir / dataset_info.name

    converter = VOCToYOLOConverter(dataset_info, dataset_output)
    split_dirs = converter.convert()

    return {
        'name': dataset_info.name,
        'classes': dataset_info.classes,
        'splits': split_dirs
    }