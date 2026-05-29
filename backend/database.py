"""
数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取后端目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 优先从环境变量读取数据库配置
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # 使用环境变量配置的数据库
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    # 默认使用 SQLite 数据库
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'rsod.db')}"
    print(f"[数据库配置] 使用默认 SQLite 数据库: {SQLALCHEMY_DATABASE_URL}")

# 创建引擎
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite 特殊配置
    )
else:
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
