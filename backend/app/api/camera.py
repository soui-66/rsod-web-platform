from fastapi import APIRouter
from pydantic import BaseModel, Field
import cv2
import numpy as np

from app.services.camera_detection_service import camera_detection_service

router = APIRouter(prefix="/api/camera", tags=["camera"])

class StartDetectionRequest(BaseModel):
    camera_id: int = Field(default=0, ge=0, description="摄像头设备ID")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="置信度阈值")
    iou_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="IOU阈值")
    inference_interval: int = Field(default=2, ge=1, description="推理间隔")

@router.post("/start")
async def start_detection(request: StartDetectionRequest):
    """启动摄像头实时检测"""
    try:
        success = camera_detection_service.start_detection(
            camera_id=request.camera_id,
            confidence_threshold=request.confidence_threshold,
            iou_threshold=request.iou_threshold,
            inference_interval=request.inference_interval
        )
        
        if success:
            return {"success": True, "message": "摄像头检测已启动"}
        else:
            return {"success": False, "message": "启动摄像头检测失败"}
    except Exception as e:
        return {"success": False, "message": f"启动失败: {str(e)}"}

@router.post("/stop")
async def stop_detection():
    """停止摄像头实时检测"""
    try:
        camera_detection_service.stop_detection()
        return {"success": True, "message": "摄像头检测已停止"}
    except Exception as e:
        return {"success": False, "message": f"停止失败: {str(e)}"}

@router.post("/pause")
async def pause_detection():
    """暂停摄像头实时检测"""
    try:
        camera_detection_service.pause_detection()
        return {"success": True, "message": "摄像头检测已暂停"}
    except Exception as e:
        return {"success": False, "message": f"暂停失败: {str(e)}"}

@router.post("/resume")
async def resume_detection():
    """恢复摄像头实时检测"""
    try:
        camera_detection_service.resume_detection()
        return {"success": True, "message": "摄像头检测已恢复"}
    except Exception as e:
        return {"success": False, "message": f"恢复失败: {str(e)}"}

@router.get("/status")
async def get_status():
    """获取摄像头检测状态"""
    return {
        "success": True,
        "data": {
            "status": camera_detection_service.status,
            "is_running": camera_detection_service.is_running
        }
    }

@router.post("/detect")
async def detect_frame(request: dict):
    """
    接收前端发送的图像并返回检测结果
    
    请求体：
        image: base64编码的图像数据
    
    返回：
        检测结果（框坐标、类别、置信度）
    """
    try:
        image_data = request.get("image")
        if not image_data:
            return {"success": False, "message": "缺少图像数据"}
        
        import base64
        
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return {"success": False, "message": "图像解码失败"}
        
        result = camera_detection_service.detect_image(image)
        
        return {
            "success": True,
            "message": "检测成功",
            "data": {
                "boxes": result.get("boxes", []),
                "frame_index": result.get("frame_index", 0),
                "fps": result.get("fps", 0),
                "detection_time": result.get("detection_time", 0),
                "total_objects": result.get("total_objects", 0)
            }
        }
    except Exception as e:
        return {"success": False, "message": f"图像检测失败: {str(e)}"}