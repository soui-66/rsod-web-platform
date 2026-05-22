#!/usr/bin/env python3
"""
YOLO11 模型训练脚本
支持训练、评估、预测功能
纯相对路径，无外部依赖
"""

import os
import argparse
import shutil
from ultralytics import YOLO


def train_model(args):
    """训练模型"""
    print("=" * 60)
    print("开始训练 YOLO 模型")
    print("=" * 60)

    model = YOLO(args.model)

    results = model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        lr0=args.lr0,
        patience=args.patience,
        name=args.name,
        amp=False,
        workers=4,
        project=".",
        exist_ok=True
    )

    print("\n训练完成！")

    # 复制最优模型到 runs/detect 目录
    target_dir = os.path.join(args.script_dir, "runs", "detect")
    os.makedirs(target_dir, exist_ok=True)

    target_best = os.path.join(target_dir, "best_model.pt")
    target_last = os.path.join(target_dir, "last_model.pt")

    src_best = os.path.join(results.save_dir, "weights", "best.pt")
    src_last = os.path.join(results.save_dir, "weights", "last.pt")

    if os.path.exists(src_best):
        shutil.copy2(src_best, target_best)
        print(f"✅ 最优模型已复制到: {target_best}")

    if os.path.exists(src_last):
        shutil.copy2(src_last, target_last)
        print(f"✅ 最终模型已复制到: {target_last}")

    return results


def evaluate_model(args):
    """评估模型"""
    print("=" * 60)
    print("开始评估模型")
    print("=" * 60)

    model = YOLO(args.model_path)
    results = model.val(data=args.data, device=args.device)

    print("\n评估完成！")
    print(f"mAP50: {results.box.map50:.4f}")
    print(f"mAP50-95: {results.box.map:.4f}")

    return results


def predict_image(args):
    """预测单张图片"""
    print("=" * 60)
    print(f"开始预测图片: {args.predict}")
    print("=" * 60)

    model = YOLO(args.model_path)
    results = model.predict(
        source=args.predict,
        conf=args.conf,
        device=args.device
    )

    for r in results:
        print(f"预测结果已保存: {r.save_dir}")

    return results


def main():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # dataset.yaml 在 script_dir 的父目录（与 datasets 同级）
    default_yaml = os.path.join(script_dir, "dataset.yaml")

    parser = argparse.ArgumentParser(description="YOLO11 模型训练脚本")

    # 训练参数
    parser.add_argument("--epochs", type=int, default=100, help="训练轮数")
    parser.add_argument("--batch", type=int, default=16, help="批次大小")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸")
    parser.add_argument("--device", type=str, default="0", help="训练设备 (cpu/0/1)")
    parser.add_argument("--lr0", type=float, default=0.01, help="初始学习率")
    parser.add_argument("--patience", type=int, default=20, help="早停耐心值")
    parser.add_argument("--data", type=str, default=default_yaml, help="数据集配置文件")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="预训练模型")
    parser.add_argument("--name", type=str, default="train", help="实验名称")

    # 评估参数
    parser.add_argument("--evaluate", action="store_true", help="仅评估模型")
    parser.add_argument("--model-path", type=str, default=None, help="待评估模型路径")

    # 预测参数
    parser.add_argument("--predict", type=str, default=None, help="预测图片路径")
    parser.add_argument("--conf", type=float, default=0.3, help="置信度阈值")

    args = parser.parse_args()
    args.script_dir = script_dir

    # 检查数据集配置文件是否存在
    if not os.path.exists(args.data):
        print(f"❌ 数据集配置文件不存在: {args.data}")
        print("请先运行 convert_voc_to_yolo.py 生成 dataset.yaml")
        return

    if args.evaluate:
        evaluate_model(args)
    elif args.predict:
        predict_image(args)
    else:
        train_model(args)


if __name__ == "__main__":
    main()