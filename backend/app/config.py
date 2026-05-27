from dotenv import load_dotenv
import os
from pydantic import BaseModel

# 加载 .env 文件里的环境变量
load_dotenv()

class Settings(BaseModel):
    """应用配置类"""

    # 应用基本信息
    app_name: str = os.getenv("APP_NAME", "遥感目标智能检测平台")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # PostgreSQL配置
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "password")
    db_name: str = os.getenv("DB_NAME", "rsod_db")

    # Redis配置
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")

    # MinIO配置
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "rsod")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() in ("true", "1", "yes")

    # YOLO模型配置
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "yolo11n.pt")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    iou_threshold: float = float(os.getenv("IOU_THRESHOLD", "0.7"))

    # 文件存储配置
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    result_dir: str = os.getenv("RESULT_DIR", "results")

    # CORS配置
    cors_origins: list = ["*"]

    # DeepSeek API配置
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_api_url: str = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")


settings = Settings()