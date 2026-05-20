#!/usr/bin/env python3
"""
YOLO11 模型训练脚本
支持训练、评估、预测功能
"""

import os
import argparse
import json
from datetime import datetime
from ultralytics import YOLO


def get_next_version(base_dir="models"):
    """自动获取下一个版本号"""
    version = "1.0.0"
    if os.path.exists(base_dir):
        versions = []
        for item in os.listdir(base_dir):
            if item.startswith("v"):
                try:
                    versions.append(item[1:])
                except:
                    pass
        if versions:
            versions.sort(key=lambda x: [int(i) for i in x.split(".")])
            last_version = versions[-1]
            parts = last_version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            version = ".".join(parts)
    return version


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
        workers=4
    )
    
    print("\n训练完成！")
    print(f"最佳模型路径: {results.save_dir}/weights/best.pt")
    print(f"最后模型路径: {results.save_dir}/weights/last.pt")
    
    # 自动复制最优模型到固定位置
    import shutil
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_best_path = os.path.join(base_dir, "runs", "detect", "best_model.pt")
    target_last_path = os.path.join(base_dir, "runs", "detect", "last_model.pt")
    
    # 确保目标目录存在
    os.makedirs(os.path.dirname(target_best_path), exist_ok=True)
    
    # 复制 best.pt
    src_best = os.path.join(results.save_dir, "weights", "best.pt")
    if os.path.exists(src_best):
        shutil.copy2(src_best, target_best_path)
        print(f"\n✅ 最优模型已复制到: {target_best_path}")
    
    # 复制 last.pt
    src_last = os.path.join(results.save_dir, "weights", "last.pt")
    if os.path.exists(src_last):
        shutil.copy2(src_last, target_last_path)
        print(f"✅ 最终模型已复制到: {target_last_path}")
    
    return results


def evaluate_model(args):
    """评估模型"""
    print("=" * 60)
    print("开始评估模型")
    print("=" * 60)
    
    model = YOLO(args.model_path)
    results = model.val(data=args.data, device=args.device)
    
    print("\n评估完成！")
    print(f"mAP50: {results.box.map:.4f}")
    print(f"mAP50-95: {results.box.map50_95:.4f}")
    
    return results


def predict_image(args):
    """预测单张图片"""
    print("=" * 60)
    print(f"开始预测图片: {args.predict}")
    print("=" * 60)
    
    model = YOLO(args.model_path if args.model_path else "yolo11n.pt")
    results = model.predict(
        source=args.predict,
        conf=args.conf,
        device=args.device
    )
    
    for r in results:
        save_path = f"prediction_{os.path.basename(args.predict)}"
        r.save(save_path)
        print(f"预测结果已保存: {save_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="YOLO11 模型训练脚本")
    
    # 训练参数
    parser.add_argument("--epochs", type=int, default=100, help="训练轮数")
    parser.add_argument("--batch", type=int, default=16, help="批次大小")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸")
    parser.add_argument("--device", type=str, default="cpu", help="训练设备 (cpu/cuda/0)")
    parser.add_argument("--lr0", type=float, default=0.01, help="初始学习率")
    parser.add_argument("--patience", type=int, default=20, help="早停耐心值")
    parser.add_argument("--data", type=str, default="rsod.yaml", help="数据集配置文件")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="预训练模型")
    parser.add_argument("--name", type=str, default="rsod_yolo11n", help="实验名称")
    parser.add_argument("--version", type=str, default=None, help="模型版本号")
    
    # 评估参数
    parser.add_argument("--evaluate", action="store_true", help="仅评估模型")
    parser.add_argument("--model-path", type=str, default=None, help="待评估模型路径")
    
    # 预测参数
    parser.add_argument("--predict", type=str, default=None, help="预测图片路径")
    parser.add_argument("--conf", type=float, default=0.3, help="置信度阈值")
    
    args = parser.parse_args()
    
    if args.evaluate:
        evaluate_model(args)
    elif args.predict:
        predict_image(args)
    else:
        train_model(args)


if __name__ == "__main__":
    main()
