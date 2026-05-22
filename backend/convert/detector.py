#!/usr/bin/env python3
"""
数据格式检测器
自动识别数据集的标注格式（VOC、COCO、YOLO等）
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum, auto
from validator import validate_raw_dataset, CheckContext, run_validators, generate_report, print_report

# 获取 backend 目录并添加到 sys.path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.utils.logger import get_logger

logger = get_logger("detector")

from app.utils.paths import Paths


class DataFormat(Enum):
    """支持的数据格式"""
    VOC = auto()
    COCO = auto()
    YOLO = auto()
    UNKNOWN = auto()


@dataclass
class DatasetInfo:
    """数据集信息"""
    name: str
    format: DataFormat
    images_dir: Optional[Path]
    labels_dir: Optional[Path]
    classes: List[str]
    num_images: int
    num_labels: int


class FormatDetector:
    """数据格式检测器"""

    IMAGE_DIR_NAMES = ['JPEGImages', 'images', 'Images', 'image', 'JPEG', 'imgs']
    LABEL_DIR_NAMES = ['Annotation', 'Annotations', 'annotations', 'annotation', 'xml', 'labels']

    def __init__(self, dataset_path: Path):
        self.dataset_path = Path(dataset_path)
        self.detected_format = DataFormat.UNKNOWN
        self.images_dir = None
        self.labels_dir = None

    def detect(self) -> DatasetInfo:
        """检测数据集格式"""
        logger.info(f"正在检测数据集: {self.dataset_path}")

        # 1. 查找图片目录
        self.images_dir = self._find_images_dir()
        if not self.images_dir:
            raise FileNotFoundError(f"未找到图片目录: {self.dataset_path}")
        logger.debug(f"图片目录: {self.images_dir}")

        # 2. 查找标注目录并检测格式
        self.detected_format, self.labels_dir = self._detect_format()
        logger.info(f"标注格式: {self.detected_format.name}")

        if self.labels_dir:
            logger.debug(f"标注目录: {self.labels_dir}")
        else:
            logger.warning("未找到标注目录")

        # 3. 获取类别信息
        classes = self._extract_classes()
        logger.info(f"发现类别: {classes}")

        # 4. 统计数量
        num_images = len(list(self.images_dir.glob('*.*')))
        num_labels = len(list(self.labels_dir.glob('*.*'))) if self.labels_dir else 0

        logger.info(f"图片数量: {num_images}, 标注数量: {num_labels}")

        return DatasetInfo(
            name=self.dataset_path.name,
            format=self.detected_format,
            images_dir=self.images_dir,
            labels_dir=self.labels_dir,
            classes=classes,
            num_images=num_images,
            num_labels=num_labels
        )

    def _find_images_dir(self) -> Optional[Path]:
        """查找图片目录"""
        for dir_name in self.IMAGE_DIR_NAMES:
            img_dir = self.dataset_path / dir_name
            if img_dir.exists() and img_dir.is_dir():
                return img_dir

        for subdir in self.dataset_path.iterdir():
            if subdir.is_dir():
                for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                    if list(subdir.glob(f'*{ext}')):
                        return subdir

        return None

    def _detect_format(self) -> Tuple[DataFormat, Optional[Path]]:
        """检测标注格式"""
        labels_dir = self._find_label_dir()

        if labels_dir:
            if self._check_voc_format(labels_dir):
                return DataFormat.VOC, labels_dir
            if self._check_coco_format(labels_dir):
                return DataFormat.COCO, labels_dir
            if self._check_yolo_format(labels_dir):
                return DataFormat.YOLO, labels_dir

        if self._check_voc_format(self.dataset_path):
            return DataFormat.VOC, self.dataset_path
        if self._check_coco_format(self.dataset_path):
            return DataFormat.COCO, self.dataset_path
        if self._check_yolo_format(self.dataset_path):
            return DataFormat.YOLO, self.dataset_path

        return DataFormat.UNKNOWN, None

    def _find_label_dir(self) -> Optional[Path]:
        """查找标注目录"""
        for dir_name in self.LABEL_DIR_NAMES:
            label_dir = self.dataset_path / dir_name
            if label_dir.exists() and label_dir.is_dir():
                # 检查是否有XML文件直接在这个目录
                if list(label_dir.glob('*.xml')):
                    return label_dir
                # 检查是否有xml子目录
                xml_subdir = label_dir / 'xml'
                if xml_subdir.exists() and list(xml_subdir.glob('*.xml')):
                    return xml_subdir
                # 检查是否有labels子目录
                labels_subdir = label_dir / 'labels'
                if labels_subdir.exists() and list(labels_subdir.glob('*.xml')):
                    return labels_subdir
        return None

    def _check_voc_format(self, directory: Path) -> bool:
        """检查是否为VOC格式（XML文件）"""
        xml_files = list(directory.glob('*.xml'))
        if not xml_files:
            return False

        try:
            tree = ET.parse(xml_files[0])
            root = tree.getroot()
            return root.find('object') is not None or root.find('filename') is not None
        except:
            return False

    def _check_coco_format(self, directory: Path) -> bool:
        """检查是否为COCO格式（JSON文件）"""
        json_files = list(directory.glob('*.json'))
        if not json_files:
            return False

        try:
            with open(json_files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
            return 'images' in data and 'annotations' in data
        except:
            return False

    def _check_yolo_format(self, directory: Path) -> bool:
        """检查是否为YOLO格式（TXT文件）"""
        txt_files = list(directory.glob('*.txt'))
        if not txt_files:
            return False

        try:
            with open(txt_files[0], 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
            parts = first_line.split()
            return len(parts) == 5 and all(self._is_float(p) for p in parts)
        except:
            return False

    def _is_float(self, s: str) -> bool:
        """检查字符串是否为浮点数"""
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _extract_classes(self) -> List[str]:
        """从标注文件中提取类别"""
        classes = set()

        if self.detected_format == DataFormat.VOC:
            classes = self._extract_voc_classes()
        elif self.detected_format == DataFormat.COCO:
            classes = self._extract_coco_classes()
        elif self.detected_format == DataFormat.YOLO:
            classes = self._extract_yolo_classes()

        return sorted(list(classes))

    def _extract_voc_classes(self) -> set:
        """从VOC XML文件中提取类别"""
        classes = set()
        if not self.labels_dir:
            return classes

        for xml_file in self.labels_dir.glob('*.xml'):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                for obj in root.findall('object'):
                    name = obj.find('name')
                    if name is not None:
                        classes.add(name.text)
            except:
                continue

        return classes

    def _extract_coco_classes(self) -> set:
        """从COCO JSON文件中提取类别"""
        classes = set()
        if not self.labels_dir:
            return classes

        for json_file in self.labels_dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for cat in data.get('categories', []):
                    classes.add(cat.get('name', ''))
            except:
                continue

        return classes

    def _extract_yolo_classes(self) -> set:
        """YOLO格式需要额外的classes.txt文件"""
        classes = set()
        classes_file = self.labels_dir / 'classes.txt' if self.labels_dir else None
        if classes_file and classes_file.exists():
            with open(classes_file, 'r', encoding='utf-8') as f:
                classes = set(line.strip() for line in f if line.strip())
        return classes


def detect_all_datasets(datasets_root: Path) -> List[DatasetInfo]:
    """检测所有数据集"""
    logger.info("=" * 60)
    logger.info("开始检测所有数据集...")
    logger.info(f"扫描目录: {datasets_root}")
    logger.info("=" * 60)

    datasets = []

    for item in datasets_root.iterdir():
        if not item.is_dir():
            continue

        if item.name in ['converted', 'train', 'test', 'val']:
            continue

        try:
            # 查找目录
            annotations_dir = item / "Annotation" / "xml"
            images_dir = item / "JPEGImages"

            # 先验证
            logger.info(f"\n验证数据集: {item.name}")
            ctx = CheckContext(
                annotations_dir=annotations_dir,
                images_dir=images_dir,
                dataset_name=item.name
            )

            validators = ["directories_exist", "annotation_files", "image_annotation_match"]
            results = run_validators(ctx, validators)
            report = generate_report(results)

            if report["has_error"]:
                logger.error(f"数据集 {item.name} 验证失败，跳过")
                print_report(report)
                continue

            print_report(report)

            # 验证通过后检测格式
            detector = FormatDetector(item)
            info = detector.detect()
            datasets.append(info)
            logger.info(f"✅ 成功检测: {info.name}")

        except Exception as e:
            logger.error(f"❌ 检测失败: {item.name} - {e}")

    return datasets


if __name__ == "__main__":
    rsod_path = Paths.rsod_data()
    if rsod_path.exists():
        datasets = detect_all_datasets(rsod_path)
        logger.info("=" * 60)
        logger.info("检测结果汇总")
        logger.info("=" * 60)
        for ds in datasets:
            logger.info(f"\n数据集: {ds.name}")
            logger.info(f"  格式: {ds.format.name}")
            logger.info(f"  类别: {ds.classes}")
            logger.info(f"  图片数: {ds.num_images}")
            logger.info(f"  标注数: {ds.num_labels}")
    else:
        logger.error(f"RSOD数据集不存在: {rsod_path}")