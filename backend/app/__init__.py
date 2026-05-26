# 遥感目标检测平台 - FastAPI 后端
from app.api import detection, validation, history, auth

__all__ = ["detection", "validation", "history", "auth"]