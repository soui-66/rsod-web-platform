# Pydantic 数据模型
from pydantic import BaseModel
from typing import Optional, List


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class DetectionResult(BaseModel):
    class_name: str
    confidence: float
    bbox: list[float]


class ValidationRequest(BaseModel):
    annotations_dir: Optional[str] = None
    images_dir: Optional[str] = None
    classes: str = "aircraft,oiltank,overpass,playground"


class DetectionBox(BaseModel):
    """检测框数据模型"""
    x1: float                # 检测框左上角X坐标
    y1: float                # 检测框左上角Y坐标
    x2: float                # 检测框右下角X坐标
    y2: float                # 检测框右下角Y坐标
    confidence: float        # 置信度 (0-1)
    class_id: int           # 类别ID
    class_name: str         # 类别名称（英文）
    chinese_name: Optional[str] = None  # 类别名称（中文）


class RealtimeDetectionResult(BaseModel):
    """实时检测结果数据模型"""
    boxes: List[DetectionBox]      # 检测框列表
    total_objects: int             # 检测到的目标总数
    detection_time: float          # 检测耗时（秒）
    image_width: int               # 图片宽度
    image_height: int              # 图片高度


class RealtimeDetectionResponse(BaseModel):
    """实时检测响应模型"""
    success: bool
    message: str
    data: Optional[RealtimeDetectionResult] = None