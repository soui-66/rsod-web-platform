#!/usr/bin/env python3
"""
YOLO11 模型训练脚本
- 使用 yolo11n.pt 预训练模型
- 最优模型保存到 runs/detect/best_model.pt（每次覆盖）
- 训练结果保存到 runs/detect/{时间戳}/
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

# 添加 backend 目录到 sys.path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.utils.paths import Paths
from app.utils.logger import setup_training_logging

logger = setup_training_logging()

from ultralytics import YOLO


def get_timestamp() -> str:
    """获取当前时间戳，格式：2026_1617"""
    return datetime.now().strftime("%Y_%m%d_%H%M")


def train_model(
    epochs: int = 100,
    batch: int = 16,
    imgsz: int = 640,
    device: str = "0",
    lr0: float = 0.01,
    patience: int = 20,
    pretrained_model: str = "yolo11n.pt"
):
    """
    训练 YOLO11 模型

    参数：
        epochs: 训练轮数
        batch: 批次大小
        imgsz: 输入图片尺寸
        device: 训练设备 (cpu/0/1)
        lr0: 初始学习率
        patience: 早停耐心值
        pretrained_model: 预训练模型路径
    """
    # ==================== 路径配置 ====================
    # 预训练模型
    model_path = Paths.backend() / pretrained_model
    if not model_path.exists():
        logger.error(f"预训练模型不存在: {model_path}")
        logger.info("请将 yolo11n.pt 放到 backend/ 目录下")
        return None

    # 数据集配置文件
    dataset_yaml = Paths.backend() / "dataset.yaml"
    if not dataset_yaml.exists():
        logger.error(f"数据集配置文件不存在: {dataset_yaml}")
        logger.info("请先运行 convert/main.py 生成 dataset.yaml")
        return None

    # 训练结果输出目录
    detect_dir = Paths.detect_results()  # runs/detect
    Paths.ensure_dir(detect_dir)

    # 本次训练的专属目录（时间戳命名）
    timestamp = get_timestamp()
    train_output_dir = detect_dir / timestamp  # runs/detect/2026_1617
    Paths.ensure_dir(train_output_dir)

    # YOLO 训练临时目录（不使用默认的 runs/train）
    yolo_project = train_output_dir / "yolo_output"

    logger.info("=" * 60)
    logger.info("开始训练 YOLO11 模型")
    logger.info("=" * 60)
    logger.info(f"预训练模型: {model_path}")
    logger.info(f"数据集配置: {dataset_yaml}")
    logger.info(f"训练轮数: {epochs}")
    logger.info(f"批次大小: {batch}")
    logger.info(f"图片尺寸: {imgsz}")
    logger.info(f"训练设备: {device}")
    logger.info(f"结果目录: {train_output_dir}")

    # ==================== 开始训练 ====================
    model = YOLO(str(model_path))

    results = model.train(
        data=str(dataset_yaml),
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        lr0=lr0,
        patience=patience,
        project=str(yolo_project),
        name="train",
        exist_ok=True,
        amp=False,
        workers=4,
        save=True,
        save_period=-1,       # 不每轮保存，只保存 best 和 last
        plots=True,           # 生成训练指标图
        val=True,
        verbose=True
    )

    # ==================== 训练后处理 ====================
    logger.info("=" * 60)
    logger.info("训练完成，整理结果...")
    logger.info("=" * 60)

    # YOLO 训练输出目录
    yolo_train_dir = yolo_project / "train"
    weights_dir = yolo_train_dir / "weights"

    # 1. 复制最优模型到 runs/detect/best_model.pt（覆盖旧模型）
    best_src = weights_dir / "best.pt"
    best_dst = detect_dir / "best_model.pt"

    if best_src.exists():
        shutil.copy2(str(best_src), str(best_dst))
        logger.info(f"最优模型已保存: {best_dst}")
    else:
        logger.warning(f"未找到最优模型: {best_src}")

    # 2. 复制最终模型到本次训练目录
    last_src = weights_dir / "last.pt"
    last_dst = train_output_dir / "last_model.pt"

    if last_src.exists():
        shutil.copy2(str(last_src), str(last_dst))
        logger.info(f"最终模型已保存: {last_dst}")

    # 3. 复制最优模型到本次训练目录（备份）
    if best_src.exists():
        best_backup = train_output_dir / "best_model.pt"
        shutil.copy2(str(best_src), str(best_backup))
        logger.info(f"最优模型备份: {best_backup}")

    # 4. 复制训练指标图到本次训练目录
    plot_files = [
        "confusion_matrix.png",
        "F1_curve.png",
        "P_curve.png",
        "R_curve.png",
        "PR_curve.png",
        "results.png",
        "results.csv",
        "labels.jpg",
        "labels_correlogram.jpg",
        "train_batch0.jpg",
        "train_batch1.jpg",
        "train_batch2.jpg",
        "val_batch0_pred.jpg",
        "val_batch0_labels.jpg",
        "val_batch1_pred.jpg",
        "val_batch1_labels.jpg",
    ]

    plots_dir = train_output_dir / "plots"
    Paths.ensure_dir(plots_dir)

    copied_plots = 0
    for plot_name in plot_files:
        src = yolo_train_dir / plot_name
        if src.exists():
            shutil.copy2(str(src), str(plots_dir / plot_name))
            copied_plots += 1

    logger.info(f"已复制 {copied_plots} 个训练指标文件到: {plots_dir}")

    # 5. 复制 args.yaml（训练参数记录）
    args_src = yolo_train_dir / "args.yaml"
    if args_src.exists():
        shutil.copy2(str(args_src), str(train_output_dir / "args.yaml"))

    # 6. 删除 YOLO 临时输出目录（已全部复制到 train_output_dir）
    if yolo_project.exists():
        shutil.rmtree(str(yolo_project))
        logger.info("已清理临时训练目录")

    # ==================== 输出训练摘要 ====================
    logger.info("=" * 60)
    logger.info("训练摘要")
    logger.info("=" * 60)

    # 读取 results.csv 获取最终指标
    results_csv = plots_dir / "results.csv"
    if results_csv.exists():
        try:
            import pandas as pd
            df = pd.read_csv(str(results_csv))
            last_row = df.iloc[-1]

            logger.info(f"最终 mAP50: {last_row.get('metrics/mAP50(B)', 'N/A')}")
            logger.info(f"最终 mAP50-95: {last_row.get('metrics/mAP50-95(B)', 'N/A')}")
            logger.info(f"最终 Precision: {last_row.get('metrics/precision(B)', 'N/A')}")
            logger.info(f"最终 Recall: {last_row.get('metrics/recall(B)', 'N/A')}")
            logger.info(f"最终 box_loss: {last_row.get('train/box_loss', 'N/A')}")
            logger.info(f"最终 cls_loss: {last_row.get('train/cls_loss', 'N/A')}")
        except Exception as e:
            logger.warning(f"无法读取训练指标: {e}")

    logger.info(f"\n最优模型: {best_dst}")
    logger.info(f"本次训练结果: {train_output_dir}")
    logger.info(f"训练指标图: {plots_dir}")

    return results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="YOLO11 模型训练脚本")
    parser.add_argument("--epochs", type=int, default=100, help="训练轮数")
    parser.add_argument("--batch", type=int, default=16, help="批次大小")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸")
    parser.add_argument("--device", type=str, default="0", help="训练设备 (cpu/0/1)")
    parser.add_argument("--lr0", type=float, default=0.01, help="初始学习率")
    parser.add_argument("--patience", type=int, default=20, help="早停耐心值")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="预训练模型")

    args = parser.parse_args()

    train_model(
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        lr0=args.lr0,
        patience=args.patience,
        pretrained_model=args.model
    )


if __name__ == "__main__":
    main()