@echo off
echo Starting YOLO11n training...
python train_model.py --data rsod_simple.yaml --model yolo11n.pt --epochs 20 --batch 8 --device cpu
pause
