from dotenv import load_dotenv
import os
from pydantic import BaseModel

# 加载 .env 文件里的环境变量
load_dotenv()

class Settings(BaseModel):
    """应用配置类"""

    # 应用基本信息
    app_name: str = os.getenv("APP_NAME")
    app_version: str = os.getenv("APP_VERSION")
    debug: bool = os.getenv("DEBUG").lower() in ("true", "1", "yes")

    # PostgreSQL配置
    db_host: str = os.getenv("DB_HOST")
    db_port: int = int(os.getenv("DB_PORT"))
    db_user: str = os.getenv("DB_USER")
    db_password: str = os.getenv("DB_PASSWORD")
    db_name: str = os.getenv("DB_NAME")

    # Redis配置
    redis_host: str = os.getenv("REDIS_HOST")
    redis_port: int = int(os.getenv("REDIS_PORT"))
    redis_password: str = os.getenv("REDIS_PASSWORD")

    # MinIO配置
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY")
    minio_bucket: str = os.getenv("MINIO_BUCKET")
    minio_secure: bool = os.getenv("MINIO_SECURE").lower() in ("true", "1", "yes")

    # YOLO模型配置
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD"))
    iou_threshold: float = float(os.getenv("IOU_THRESHOLD"))

    # 文件存储配置
    upload_dir: str = os.getenv("UPLOAD_DIR")
    result_dir: str = os.getenv("RESULT_DIR")

    # CORS配置
    cors_origins: list = ["*"]


settings = Settings()