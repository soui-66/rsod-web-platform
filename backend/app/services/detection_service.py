# 检测服务
import os
import uuid
import json
import base64
from io import BytesIO
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw
from ultralytics import YOLO


class DetectionService:
    def __init__(self, model_path: str, base_dir: str):
        self.model = YOLO(model_path)
        self.base_dir = base_dir
        self.static_dir = os.path.join(base_dir, "static")

    def detect_single_image(self, file_content: bytes) -> dict:
        """单图检测"""
        start_time = datetime.now()

        # 原图转 base64
        original_b64 = base64.b64encode(file_content).decode("utf-8")
        original_url = f"data:image/jpeg;base64,{original_b64}"

        # 保存临时文件用于推理
        temp_path = os.path.join(self.static_dir, f"temp_{uuid.uuid4().hex}.jpg")
        with open(temp_path, "wb") as f:
            f.write(file_content)

        # YOLO 推理
        results = self.model(temp_path, save=False)

        # 生成标注图
        img = Image.open(BytesIO(file_content))
        draw = ImageDraw.Draw(img)

        detections = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls = self.model.names[int(box.cls[0])]
            conf = float(box.conf[0])
            detections.append({
                "class": cls,
                "confidence": conf,
                "bbox": [float(v) for v in box.xyxy[0].tolist()]
            })
            draw.rectangle([x1, y1, x2, y2], outline="#00FF00", width=3)
            draw.text((x1, max(y1 - 20, 0)), f"{cls} {conf:.2f}", fill="#00FF00")

        # 结果图转 base64
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        result_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        result_url = f"data:image/jpeg;base64,{result_b64}"

        # 统计
        target_count = len(detections)
        max_confidence = max([d["confidence"] for d in detections]) if detections else 0.0
        duration = (datetime.now() - start_time).total_seconds()

        # 删除临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return {
            "original_url": original_url,
            "result_url": result_url,
            "detections": detections,
            "target_count": target_count,
            "max_confidence": max_confidence,
            "duration": duration
        }

    def detect_batch_images(self, files: list) -> list:
        """批量检测"""
        results = []
        for file in files:
            file_content = file.read()
            result = self.detect_single_image(file_content)
            result["file_name"] = file.filename
            results.append(result)
        return results

    def detect_video(self, video_content: bytes, video_filename: str) -> dict:
        """视频检测"""
        import cv2

        start_time = datetime.now()

        # 保存上传的视频文件
        video_path = os.path.join(self.static_dir, f"temp_video_{uuid.uuid4().hex}.mp4")
        with open(video_path, "wb") as f:
            f.write(video_content)

        print(f"[视频检测] 上传视频大小: {len(video_content) / 1024 / 1024:.2f} MB")

        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("无法打开视频文件")

        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"[视频检测] 视频信息: {width}x{height}, {fps} FPS, {total_frames} 帧")

        # 创建输出视频写入器
        output_video_filename = f"output_video_{uuid.uuid4().hex}.mp4"
        output_video_path = os.path.join(self.static_dir, output_video_filename)

        # 尝试使用H.264编码
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        if not out.isOpened():
            print("[视频检测] H.264编码不可用，尝试MP4V编码")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        if not out.isOpened():
            raise Exception("无法创建视频写入器")

        frame_index = 0
        all_detections = []
        total_targets = 0
        processed_frames = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 将帧转换为JPEG图片用于推理
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                frame_index += 1
                continue

            frame_content = buffer.tobytes()

            # 保存临时文件用于推理
            temp_frame_path = os.path.join(self.static_dir, f"temp_frame_{uuid.uuid4().hex}.jpg")
            with open(temp_frame_path, "wb") as f:
                f.write(frame_content)

            # YOLO 推理
            try:
                yolo_result = self.model(temp_frame_path, save=False)

                frame_detections = []
                for box in yolo_result[0].boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cls = self.model.names[int(box.cls[0])]
                    conf = float(box.conf[0])
                    frame_detections.append({
                        "class": cls,
                        "confidence": conf,
                        "bbox": [float(v) for v in box.xyxy[0].tolist()]
                    })
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 3)
                    label = f"{cls} {conf:.2f}"
                    cv2.putText(frame, label, (int(x1), max(int(y1) - 10, 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                target_count = len(frame_detections)
                total_targets += target_count

                for det in frame_detections[:5]:
                    det["frame_index"] = frame_index + 1
                all_detections.extend(frame_detections[:5])

                processed_frames += 1

            except Exception as e:
                print(f"帧 {frame_index} 处理失败: {str(e)}")

            if os.path.exists(temp_frame_path):
                os.remove(temp_frame_path)

            out.write(frame)
            frame_index += 1

        print(f"[视频检测] 处理完成: {processed_frames} 帧, {total_targets} 个目标")

        cap.release()
        out.release()

        import time
        time.sleep(1)

        if os.path.exists(video_path):
            os.remove(video_path)

        if not os.path.exists(output_video_path):
            raise Exception("输出视频文件不存在")

        file_size = os.path.getsize(output_video_path)
        print(f"[视频检测] 输出视频大小: {file_size / 1024 / 1024:.2f} MB")

        output_video_url = f"http://localhost:8000/static/{output_video_filename}"
        print(f"[视频检测] 输出视频URL: {output_video_url}")

        duration = (datetime.now() - start_time).total_seconds()

        return {
            "video_url": output_video_url,
            "total_frames": processed_frames,
            "total_targets": total_targets,
            "duration": duration,
            "detections": all_detections[:200]
        }