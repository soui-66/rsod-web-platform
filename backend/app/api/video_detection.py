"""
视频检测 API 路由
"""
import os
import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse

# 导入检测服务（用于实时检测）
from app.services.detection_service import DetectionService

# 导入数据模型
from app.models.schemas import (
    RealtimeDetectionResponse,
)

# 创建API路由实例
router = APIRouter(prefix="/api/video-detection", tags=["视频检测"])

# 获取BASE_DIR
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BASE_DIR)
BASE_DIR = os.path.dirname(BASE_DIR)

# 单例检测服务
_detection_service = None

def get_detection_service():
    """获取检测服务实例（单例）"""
    global _detection_service
    if _detection_service is None:
        model_path = os.path.join(BASE_DIR, "runs", "detect", "best_model.pt")
        _detection_service = DetectionService(model_path, BASE_DIR)
        print("[视频检测接口] 检测服务初始化完成")
    return _detection_service


# =============================================================================
# 实时视频帧检测接口
# =============================================================================
@router.post("/realtime-frame", response_model=RealtimeDetectionResponse)
async def detect_realtime_frame(
    file: UploadFile = File(...), description="视频帧图片文件",
    model_name: str = Form("rsod-yolo11n", description="模型名称"),
    confidence_threshold: float = Form(0.25, description="置信度阈值"),
    iou_threshold: float = Form(0.7, description="IOU阈值")
):
    """
    实时视频帧检测接口

    功能：
    - 接收视频播放时的单帧图片
    - 使用RSOD模型进行目标检测
    - 返回检测结果（不保存到数据库）

    参数：
        file: 视频帧图片文件
        model_name: 模型名称
        confidence_threshold: 置信度阈值
        iou_threshold: IOU阈值

    返回：
        RealtimeDetectionResponse: 检测结果
    """
    try:
        # 读取上传的文件内容
        contents = await file.read()

        # 使用OpenCV解码图片
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 检查图片是否成功解码
        if image is None:
            raise HTTPException(status_code=400, detail="无法解析图片")

        # 获取检测服务
        detection_service = get_detection_service()

        # 进行检测（快速模式，不保存到数据库）
        result = detection_service.detect_frame_realtime(
            image=image,
            model_name=model_name,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold
        )

        # 返回成功的响应
        return RealtimeDetectionResponse(
            success=True,
            message="检测成功",
            data=result
        )

    except HTTPException:
        # 重新抛出HTTP异常（已经是正确的格式）
        raise
    except Exception as e:
        # 捕获其他异常并返回500错误
        import traceback
        print(f"[实时帧检测错误] 异常类型: {type(e).__name__}")
        print(f"[实时帧检测错误] 异常信息: {str(e)}")
        print(f"[实时帧检测错误] 堆栈信息: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"实时帧检测失败: {str(e)}"
        )
