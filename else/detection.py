# 检测接口
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import json

from database import get_db
from models import DetectionRecord, ModelVersion
from app.services.detection_service import DetectionService

router = APIRouter(prefix="/api/inference", tags=["目标检测"])

# 获取BASE_DIR
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BASE_DIR)
BASE_DIR = os.path.dirname(BASE_DIR)

# 检测服务缓存（支持多模型）
_detection_services = {}


def get_detection_service(model_id: int = None, db: Session = None):
    """获取检测服务实例（支持多模型缓存）"""
    global _detection_services
    
    # 如果 model_id 为 0 或 None，使用默认模型
    cache_key = model_id if model_id else "default"
    
    if cache_key not in _detection_services:
        model_name = "本地默认模型"
        model_path = os.path.join(BASE_DIR, "runs", "detect", "best_model.pt")
        
        if model_id and model_id != 0 and db:
            model_version = db.query(ModelVersion).filter(
                ModelVersion.id == model_id,
                ModelVersion.is_active == True
            ).first()
            
            if model_version:
                model_path = model_version.file_path
                model_name = model_version.name
                print(f"[检测接口] 使用指定模型: {model_version.name} (ID: {model_id})")
            else:
                print(f"[检测接口] 未找到ID为 {model_id} 的模型，使用默认模型")
        else:
            print("[检测接口] 使用本地默认模型")
        
        _detection_services[cache_key] = {
            'service': DetectionService(model_path, BASE_DIR),
            'model_name': model_name
        }
        print(f"[检测接口] 检测服务初始化完成，缓存键: {cache_key}")
    
    return _detection_services[cache_key]


@router.post("/single")
async def inference_single(
        file: UploadFile = File(...),
        confidence_threshold: float = Form(0.25),
        user_id: int = Form(None),
        selected_model_id: int = Form(None),
        db: Session = Depends(get_db)
):
    """单图目标检测接口"""
    print(f"\n[检测接口] 收到单图检测请求")
    print(f"[检测接口] 文件名: {file.filename}")
    print(f"[检测接口] 用户ID: {user_id}")
    print(f"[检测接口] 模型ID: {selected_model_id}")
    print(f"[检测接口] 置信度阈值: {confidence_threshold}")

    try:
        file_content = await file.read()
        print(f"[检测接口] 文件大小: {len(file_content)} bytes")

        service_data = get_detection_service(selected_model_id, db)
        service = service_data['service']
        model_name = service_data['model_name']
        print(f"[检测接口] 检测服务获取成功，模型: {model_name}")

        result = service.detect_single_image(file_content, confidence_threshold=confidence_threshold)
        print(f"[检测接口] 检测完成，目标数量: {result['target_count']}")

        record = DetectionRecord(
            user_id=user_id,
            file_name=file.filename,
            original_image=result["original_url"],
            result_image=result["result_url"],
            mode="single",
            model_name=model_name,
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

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"code": e.status_code, "message": e.detail}
        )
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
        confidence_threshold: float = Form(0.25),
        user_id: int = Form(None),
        selected_model_id: int = Form(None),
        db: Session = Depends(get_db)
):
    """批量目标检测接口"""
    try:
        start_time = datetime.now()

        service_data = get_detection_service(selected_model_id, db)
        service = service_data['service']
        model_name = service_data['model_name']

        results = []
        total_target_count = 0
        batch_detections = []

        for file in files:
            file_content = await file.read()
            result = service.detect_single_image(file_content, confidence_threshold=confidence_threshold)

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

        record = DetectionRecord(
            user_id=user_id,
            file_name=f"批量检测_{len(files)}张",
            original_image=results[0]["original_url"] if results else "",
            result_image=results[0]["image_url"] if results else "",
            mode="batch",
            model_name=model_name,
            detections=json.dumps(batch_detections, ensure_ascii=False),
            target_count=total_target_count,
            duration=duration,
            max_confidence=max([r["max_confidence"] for r in results]) if results else 0.0,
            batch_data=json.dumps(results, ensure_ascii=False)
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

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"code": e.status_code, "message": e.detail}
        )
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
        confidence_threshold: float = Form(0.25),
        user_id: int = Form(None),
        selected_model_id: int = Form(None),
        db: Session = Depends(get_db)
):
    """视频目标检测接口"""
    try:
        service_data = get_detection_service(selected_model_id, db)
        service = service_data['service']
        model_name = service_data['model_name']

        video_content = await video.read()
        video_filename = video.filename or "video_detection"

        result = service.detect_video(video_content, video_filename, confidence_threshold=confidence_threshold)

        record = DetectionRecord(
            user_id=user_id,
            file_name=video_filename,
            original_image="",
            result_image=result["video_url"],
            mode="video",
            model_name=model_name,
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

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"code": e.status_code, "message": e.detail}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"视频检测失败: {str(e)}"}
        )