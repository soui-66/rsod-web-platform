# 检测接口
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import json

from database import get_db
from models import DetectionRecord
from app.services.detection_service import DetectionService

router = APIRouter(prefix="/api/inference", tags=["目标检测"])

# 获取BASE_DIR
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 回到backend目录: backend/app/api -> backend/app -> backend
BASE_DIR = os.path.dirname(BASE_DIR)
BASE_DIR = os.path.dirname(BASE_DIR)


def get_detection_service():
    """获取检测服务实例"""
    model_path = os.path.join(BASE_DIR, "runs", "detect", "best_model.pt")
    return DetectionService(model_path, BASE_DIR)


@router.post("/single")
async def inference_single(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    单图目标检测接口

    上传一张图片，返回检测结果和标注后的图片
    """
    try:
        # 读取图片
        file_content = await file.read()

        # 检测服务
        service = get_detection_service()
        result = service.detect_single_image(file_content)

        # 存入数据库
        record = DetectionRecord(
            file_name=file.filename,
            original_image=result["original_url"],
            result_image=result["result_url"],
            mode="single",
            detections=json.dumps(result["detections"], ensure_ascii=False),
            target_count=result["target_count"],
            duration=result["duration"],
            max_confidence=result["max_confidence"]
        )
        db.add(record)
        db.commit()

        return {
            "code": 200,
            "message": "推理成功",
            "data": {
                "detections": result["detections"],
                "image_url": result["result_url"],
                "original_url": result["original_url"],
                "record_id": record.id,
                "target_count": result["target_count"],
                "duration": result["duration"]
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"推理失败: {str(e)}"}
        )


@router.post("/batch")
async def inference_batch(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    批量目标检测接口

    上传多张图片，返回所有图片的检测结果
    """
    try:
        start_time = datetime.now()

        service = get_detection_service()
        results = []
        total_target_count = 0
        batch_detections = []

        for file in files:
            file_content = await file.read()
            result = service.detect_single_image(file_content)

            results.append({
                "file_name": file.filename,
                "detections": result["detections"],
                "image_url": result["result_url"],
                "original_url": result["original_url"],
                "target_count": result["target_count"],
                "max_confidence": result["max_confidence"]
            })

            total_target_count += result["target_count"]
            batch_detections.extend([{**d, "file_name": file.filename} for d in result["detections"]])

        duration = (datetime.now() - start_time).total_seconds()

        # 存入数据库
        record = DetectionRecord(
            file_name=f"批量检测_{len(files)}张",
            original_image="",
            result_image="",
            mode="batch",
            detections=json.dumps(batch_detections, ensure_ascii=False),
            target_count=total_target_count,
            duration=duration,
            max_confidence=max([r["max_confidence"] for r in results]) if results else 0.0
        )
        db.add(record)
        db.commit()

        return {
            "code": 200,
            "message": f"批量推理成功，共处理 {len(files)} 张图片",
            "data": {
                "results": results,
                "record_id": record.id,
                "total_images": len(files),
                "total_targets": total_target_count,
                "duration": duration
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"批量推理失败: {str(e)}"}
        )


@router.post("/video")
async def inference_video(
    video: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    视频目标检测接口

    对视频的每一帧进行目标检测，输出带有识别框的完整视频
    """
    try:
        service = get_detection_service()

        # 读取视频内容
        video_content = await video.read()
        video_filename = video.filename or "video_detection"

        # 执行视频检测
        result = service.detect_video(video_content, video_filename)

        # 存入数据库
        record = DetectionRecord(
            file_name=video_filename,
            original_image="",
            result_image=result["video_url"],
            mode="video",
            detections=json.dumps(result["detections"][:100], ensure_ascii=False),
            target_count=result["total_targets"],
            duration=result["duration"],
            max_confidence=max([d["confidence"] for d in result["detections"]]) if result["detections"] else 0.0
        )
        db.add(record)
        db.commit()

        return {
            "code": 200,
            "message": f"视频检测完成，共处理 {result['total_frames']} 帧",
            "data": {
                "video_url": result["video_url"],
                "record_id": record.id,
                "total_frames": result["total_frames"],
                "total_targets": result["total_targets"],
                "duration": result["duration"],
                "detections": result["detections"]
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"视频检测失败: {str(e)}"}
        )