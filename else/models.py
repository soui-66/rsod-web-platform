from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.schema import Sequence
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, Sequence('users_id_seq'), primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    created_at = Column(DateTime, default=datetime.now)


class DetectionRecord(Base):
    __tablename__ = "detection_records"
    id = Column(Integer, Sequence('detection_records_id_seq'), primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    file_name = Column(String(255), nullable=False)
    original_image = Column(Text, nullable=False)
    result_image = Column(Text, nullable=True)
    mode = Column(String(20), default="single")
    model_name = Column(String(50), default="yolo11n")
    detections = Column(Text, nullable=True)
    target_count = Column(Integer, default=0)
    duration = Column(Float, default=0.0)
    max_confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    batch_data = Column(Text, nullable=True)


class ChatRecord(Base):
    __tablename__ = "chat_records"
    id = Column(Integer, Sequence('chat_records_id_seq'), primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    model_type = Column(String(50), default="yolo")
    version = Column(String(20), default="1.0")
    accuracy = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)