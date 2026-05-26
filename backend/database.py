"""
数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = "sqlite:///./rsod_platform.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
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
        # 导入模型以确保它们被注册到 Base.metadata
        from models import DetectionRecord, User
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        # 验证表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "detection_records" in tables:
            print("✅ detection_records 表已创建")
            # 检查 batch_data 字段是否存在
            columns = [col['name'] for col in inspector.get_columns('detection_records')]
            if 'batch_data' in columns:
                print("✅ batch_data 字段已存在")
            else:
                print("⚠️  batch_data 字段不存在，需要运行迁移脚本")
        else:
            print("❌ detection_records 表未创建")
            
        if "users" in tables:
            print("✅ users 表已创建")
        else:
            print("❌ users 表未创建")
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        raise