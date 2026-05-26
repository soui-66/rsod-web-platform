# Pydantic 数据模型
from pydantic import BaseModel
from typing import Optional


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