"""
数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 从环境变量读取数据库配置，默认使用 PostgreSQL
POSTGRES_USER = os.getenv("POSTGRES_USER", "rsod_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rsod_password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "rsod_db")

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    try:
        from models import DetectionRecord, User, ChatRecord, TargetCategory, ModelVersion

        Base.metadata.create_all(bind=engine)

        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if "detection_records" in tables:
            print("[OK] detection_records 表已创建")
            columns = [col['name'] for col in inspector.get_columns('detection_records')]
            if 'batch_data' in columns:
                print("[OK] batch_data 字段已存在")
            else:
                print("[WARN] batch_data 字段不存在，需要运行迁移脚本")
        else:
            print("[ERROR] detection_records 表未创建")

        if "users" in tables:
            print("[OK] users 表已创建")
        else:
            print("[ERROR] users 表未创建")

        if "chat_records" in tables:
            print("[OK] chat_records 表已创建")
        else:
            print("[ERROR] chat_records 表未创建")

        if "target_categories" in tables:
            print("[OK] target_categories 表已创建")
        else:
            print("[ERROR] target_categories 表未创建")

        if "model_versions" in tables:
            print("[OK] model_versions 表已创建")
        else:
            print("[ERROR] model_versions 表未创建")
            
    except Exception as e:
        print("[ERROR] 数据库初始化失败: %s" % str(e))
        raise