#!/usr/bin/env python3
"""
数据转换主程序
1. 检测原始数据格式
2. 调用对应转换器
3. 生成dataset.yaml
"""

import sys
from pathlib import Path

# 添加 backend 目录到 sys.path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.utils.paths import Paths
from app.utils.logger import setup_converter_logging

logger = setup_converter_logging()

from detector import FormatDetector, DataFormat, detect_all_datasets
from converter_voc import convert_voc_dataset


def generate_dataset_yaml(converted_results: list, output_path: Path):
    """生成YOLO数据集配置文件"""
    # 收集所有类别（按出现顺序）
    all_classes = []
    class_set = set()
    for result in converted_results:
        for cls in result['classes']:
            if cls not in class_set:
                all_classes.append(cls)
                class_set.add(cls)

    yaml_content = f"""# 自动生成的 YOLO 数据集配置文件
# 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# 类别数量
nc: {len(all_classes)}

# 类别名称
names:
"""

    for idx, name in enumerate(all_classes):
        yaml_content += f"  {idx}: {name}\n"

    yaml_content += f"""
# 数据集路径（相对于此配置文件）
path: converted

# 训练集路径
train:
"""
    for result in converted_results:
        yaml_content += f"  - {result['name']}/train/images\n"

    yaml_content += "val:\n"
    for result in converted_results:
        yaml_content += f"  - {result['name']}/val/images\n"

    yaml_content += "test:\n"
    for result in converted_results:
        yaml_content += f"  - {result['name']}/test/images\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    logger.info(f"dataset.yaml 已生成: {output_path}")


def main():
    """主程序"""
    logger.info("=" * 60)
    logger.info("数据集转换工具启动")
    logger.info("=" * 60)

    # 获取路径
    datasets_dir = Paths.datasets()      # backend/datasets
    rsod_dir = Paths.rsod_data()        # backend/datasets/rsod
    converted_dir = datasets_dir / "converted"

    # 确保目录存在
    Paths.ensure_dir(converted_dir)

    logger.info(f"原始数据目录: {rsod_dir}")
    logger.info(f"转换输出目录: {converted_dir}")

    # 1. 检测所有数据集
    if not rsod_dir.exists():
        logger.error(f"RSOD数据目录不存在: {rsod_dir}")
        return

    datasets = detect_all_datasets(rsod_dir)

    if not datasets:
        logger.warning("未检测到任何数据集")
        return

    logger.info(f"共检测到 {len(datasets)} 个数据集")

    # 2. 创建全局类别映射（关键修复）
    all_classes = []
    class_set = set()
    for ds_info in datasets:
        for cls in ds_info.classes:
            if cls not in class_set:
                all_classes.append(cls)
                class_set.add(cls)

    # 创建全局类别映射（所有数据集共用）
    global_class_map = {name: idx for idx, name in enumerate(all_classes)}

    logger.info(f"全局类别映射: {global_class_map}")

    # 3. 根据格式调用对应转换器
    converted_results = []

    for ds_info in datasets:
        logger.info("=" * 60)
        logger.info(f"处理数据集: {ds_info.name}")
        logger.info("=" * 60)

        if ds_info.format == DataFormat.VOC:
            logger.info(f"检测到VOC格式，开始转换...")
            # 传入全局 class_map
            result = convert_voc_dataset(ds_info, converted_dir, global_class_map)
            if result:
                converted_results.append(result)
                logger.info(f"{ds_info.name} 转换完成")
        elif ds_info.format == DataFormat.COCO:
            logger.warning(f"COCO格式转换器尚未实现: {ds_info.name}")
        elif ds_info.format == DataFormat.YOLO:
            logger.info(f"数据已是YOLO格式，无需转换: {ds_info.name}")
        else:
            logger.error(f"未知格式，无法转换: {ds_info.name}")

    # 4. 生成dataset.yaml
    if converted_results:
        yaml_path = Paths.backend() / "dataset.yaml"
        generate_dataset_yaml(converted_results, yaml_path)

        logger.info("=" * 60)
        logger.info("全部转换完成！")
        logger.info("=" * 60)
        logger.info(f"转换后的数据: {converted_dir}")
        logger.info(f"配置文件: {yaml_path}")
        logger.info(f"训练命令: python train.py --data {yaml_path}")
    else:
        logger.error("没有成功转换的数据集")


if __name__ == "__main__":
    main()