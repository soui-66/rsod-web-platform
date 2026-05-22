"""
遥感目标检测平台 - FastAPI 后端
"""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from ultralytics import YOLO
from passlib.context import CryptContext
from pathlib import Path
import os
import uuid
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw

from database import get_db, init_db
from models import DetectionRecord, User
from app.utils.validation import CheckContext, DataValidator

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], default="pbkdf2_sha256", deprecated="auto")

app = FastAPI(
    title="遥感目标智能检测平台",
    description="基于YOLO11的遥感图像目标检测系统API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)

# 自定义静态文件服务，添加CORS头
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

class StaticFilesWithCORS(StaticFiles):
    async def __call__(self, scope, receive, send):
        # 添加CORS头
        response = await super().__call__(scope, receive, send)
        return response

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 添加静态文件CORS中间件
@app.middleware("http")
async def add_static_cors_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

model = YOLO("runs/detect/best_model.pt")


@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ 数据库初始化完成")


@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "healthy", "service": "rsod-web-platform", "version": "1.0.0"}


@app.post("/api/validate/dataset", tags=["数据验证"])
async def validate_dataset(
    annotations_dir: str = None,
    images_dir: str = None,
    classes: str = "aircraft,oiltank,overpass,playground"
):
    """
    数据集验证接口

    用于验证数据集的完整性和一致性

    参数：
        annotations_dir: 标注文件目录路径（可选）
        images_dir: 图片文件目录路径（可选）
        classes: 期望的类别列表，逗号分隔

    返回：
        验证报告，包含所有检查结果
    """
    # 确定标注目录和图片目录
    if annotations_dir:
        annotations_path = Path(annotations_dir)
    else:
        annotations_path = Path(BASE_DIR) / "datasets" / "rsod"

    if images_dir:
        images_path = Path(images_dir)
    else:
        images_path = Path(BASE_DIR) / "datasets" / "rsod"

    # 解析类别列表
    class_list = [c.strip() for c in classes.split(",") if c.strip()]

    # 创建验证上下文
    context = CheckContext(
        annotations_dir=annotations_path if annotations_path.exists() else None,
        images_dir=images_path if images_path.exists() else None,
        classes=class_list if class_list else None,
        image_extensions=[".jpg", ".jpeg", ".png"]
    )

    # 执行验证
    validator = DataValidator(context)
    report = validator.validate()

    # 构建返回结果
    results = []
    for result in report.results:
        results.append({
            "level": result.level.value,
            "message": result.message,
            "check_name": result.check_name,
            "details": result.details
        })

    return {
        "code": 200,
        "message": "数据验证完成",
        "data": {
            "passed": report.passed,
            "summary": {
                "passed": report.pass_count,
                "warnings": report.warning_count,
                "errors": report.error_count
            },
            "results": results
        }
    }


@app.get("/", tags=["根路径"])
async def root():
    return {"message": "欢迎使用遥感目标智能检测平台"}


@app.post("/api/inference/batch")
async def inference_batch(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    try:
        start_time = datetime.now()
        
        results = []
        total_target_count = 0
        batch_detections = []
        
        for file in files:
            file_content = await file.read()
            
            # 原图转 base64
            original_b64 = base64.b64encode(file_content).decode("utf-8")
            original_url = f"data:image/jpeg;base64,{original_b64}"
            
            # 保存临时文件用于推理
            temp_path = os.path.join(BASE_DIR, "static", f"temp_{uuid.uuid4().hex}.jpg")
            with open(temp_path, "wb") as f:
                f.write(file_content)
            
            # YOLO 推理
            result = model(temp_path, save=False)
            
            # 生成标注图
            img = Image.open(BytesIO(file_content))
            draw = ImageDraw.Draw(img)
            
            detections = []
            for box in result[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls = model.names[int(box.cls[0])]
                conf = float(box.conf[0])
                detections.append({
                    "class": cls,
                    "confidence": conf,
                    "bbox": [float(v) for v in box.xyxy[0].tolist()]
                })
                draw.rectangle([x1, y1, x2, y2], outline="#00FF00", width=3)
                draw.text((x1, max(y1 - 20, 0)), f"{cls} {conf:.2f}", fill="#00FF00")
            
            # 结果图转 base64
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            result_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            result_url = f"data:image/jpeg;base64,{result_b64}"
            
            # 统计
            target_count = len(detections)
            total_target_count += target_count
            max_confidence = max([d["confidence"] for d in detections]) if detections else 0.0
            
            # 收集单张图片结果
            results.append({
                "file_name": file.filename,
                "detections": detections,
                "image_url": result_url,
                "original_url": original_url,
                "target_count": target_count,
                "max_confidence": max_confidence
            })
            
            # 收集检测信息用于数据库
            batch_detections.extend([{**d, "file_name": file.filename} for d in detections])
            
            # 删除临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        # 计算总耗时
        duration = (datetime.now() - start_time).total_seconds()
        
        # 存入数据库（批量记录）
        record = DetectionRecord(
            file_name=f"批量检测_{len(files)}张",
            original_image="",
            result_image="",
            mode="batch",
            detections=json.dumps(batch_detections, ensure_ascii=False),
            target_count=total_target_count,
            duration=duration,
            max_confidence=max([r["max_confidence"] for r in results]) if results else 0.0
        )
        db.add(record)
        db.commit()
        
        return {
            "code": 200,
            "message": f"批量推理成功，共处理 {len(files)} 张图片",
            "data": {
                "results": results,
                "record_id": record.id,
                "total_images": len(files),
                "total_targets": total_target_count,
                "duration": duration
            }
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"批量推理失败: {str(e)}"}
        )


@app.post("/api/inference/single")
async def inference_single(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        start_time = datetime.now()

        # 1. 读取图片
        file_content = await file.read()

        # 2. 原图转 base64
        original_b64 = base64.b64encode(file_content).decode("utf-8")
        original_url = f"data:image/jpeg;base64,{original_b64}"

        # 3. 保存临时文件用于推理
        temp_path = os.path.join(BASE_DIR, "static", f"temp_{uuid.uuid4().hex}.jpg")
        with open(temp_path, "wb") as f:
            f.write(file_content)

        # 4. YOLO 推理（不保存文件）
        results = model(temp_path, save=False)

        # 5. 生成标注图
        img = Image.open(BytesIO(file_content))
        draw = ImageDraw.Draw(img)

        detections = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls = model.names[int(box.cls[0])]
            conf = float(box.conf[0])
            detections.append({
                "class": cls,
                "confidence": conf,
                "bbox": [float(v) for v in box.xyxy[0].tolist()]
            })
            draw.rectangle([x1, y1, x2, y2], outline="#00FF00", width=3)
            draw.text((x1, max(y1 - 20, 0)), f"{cls} {conf:.2f}", fill="#00FF00")

        # 结果图转 base64
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        result_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        result_url = f"data:image/jpeg;base64,{result_b64}"

        # 6. 统计
        target_count = len(detections)
        max_confidence = max([d["confidence"] for d in detections]) if detections else 0.0
        duration = (datetime.now() - start_time).total_seconds()

        # 7. 存入数据库
        record = DetectionRecord(
            file_name=file.filename,
            original_image=original_url,
            result_image=result_url,
            mode="single",
            detections=json.dumps(detections, ensure_ascii=False),
            target_count=target_count,
            duration=duration,
            max_confidence=max_confidence
        )
        db.add(record)
        db.commit()

        # 8. 删除临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return {
            "code": 200,
            "message": "推理成功",
            "data": {
                "detections": detections,
                "image_url": result_url,
                "original_url": original_url,
                "record_id": record.id,
                "target_count": target_count,
                "duration": duration
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"推理失败: {str(e)}"}
        )


# ==================== 视频检测接口 ====================
@app.post("/api/inference/video")
async def inference_video(
    video: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    视频目标检测接口

    对视频的每一帧进行目标检测，输出带有识别框的完整视频
    """
    try:
        import cv2
        import numpy as np
        from datetime import datetime
        
        start_time = datetime.now()
        
        # 1. 保存上传的视频文件
        video_path = os.path.join(BASE_DIR, "static", f"temp_video_{uuid.uuid4().hex}.mp4")
        video_content = await video.read()
        with open(video_path, "wb") as f:
            f.write(video_content)
        
        print(f"[视频检测] 上传视频大小: {len(video_content) / 1024 / 1024:.2f} MB")
        
        # 2. 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("无法打开视频文件")
        
        # 3. 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"[视频检测] 视频信息: {width}x{height}, {fps} FPS, {total_frames} 帧")
        
        # 4. 创建输出视频写入器
        output_video_filename = f"output_video_{uuid.uuid4().hex}.mp4"
        output_video_path = os.path.join(BASE_DIR, "static", output_video_filename)
        
        # 尝试使用H.264编码（更兼容浏览器）
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264编码
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        # 如果H.264不可用，回退到mp4v
        if not out.isOpened():
            print("[视频检测] H.264编码不可用，尝试MP4V编码")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            raise Exception("无法创建视频写入器")
        
        frame_index = 0
        all_detections = []
        total_targets = 0
        processed_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 将帧转换为JPEG图片用于推理
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                frame_index += 1
                continue
            
            frame_content = buffer.tobytes()
            
            # 保存临时文件用于推理
            temp_frame_path = os.path.join(BASE_DIR, "static", f"temp_frame_{uuid.uuid4().hex}.jpg")
            with open(temp_frame_path, "wb") as f:
                f.write(frame_content)
            
            # YOLO 推理
            try:
                yolo_result = model(temp_frame_path, save=False)
                
                # 在原始帧上绘制检测框（使用OpenCV直接绘制）
                frame_detections = []
                for box in yolo_result[0].boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cls = model.names[int(box.cls[0])]
                    conf = float(box.conf[0])
                    frame_detections.append({
                        "class": cls,
                        "confidence": conf,
                        "bbox": [float(v) for v in box.xyxy[0].tolist()]
                    })
                    # 使用OpenCV绘制矩形框和标签
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 3)
                    label = f"{cls} {conf:.2f}"
                    cv2.putText(frame, label, (int(x1), max(int(y1) - 10, 10)), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # 统计
                target_count = len(frame_detections)
                total_targets += target_count
                
                # 收集所有检测结果（每帧最多保存5个）
                for det in frame_detections[:5]:
                    det["frame_index"] = frame_index + 1
                all_detections.extend(frame_detections[:5])
                
                processed_frames += 1
                
            except Exception as e:
                print(f"帧 {frame_index} 处理失败: {str(e)}")
            
            # 删除临时帧文件
            if os.path.exists(temp_frame_path):
                os.remove(temp_frame_path)
            
            # 写入处理后的帧到输出视频
            out.write(frame)
            frame_index += 1
        
        print(f"[视频检测] 处理完成: {processed_frames} 帧, {total_targets} 个目标")
        
        # 5. 释放资源
        cap.release()
        out.release()
        
        # 等待视频文件写入完成
        import time
        time.sleep(1)
        
        # 6. 删除临时视频文件
        if os.path.exists(video_path):
            os.remove(video_path)
        
        # 检查输出视频文件
        if not os.path.exists(output_video_path):
            raise Exception("输出视频文件不存在")
        
        file_size = os.path.getsize(output_video_path)
        print(f"[视频检测] 输出视频大小: {file_size / 1024 / 1024:.2f} MB")
        
        # 生成视频URL（通过静态文件服务访问）
        output_video_url = f"http://localhost:8000/static/{output_video_filename}"
        
        print(f"[视频检测] 输出视频URL: {output_video_url}")
        
        # 8. 计算总耗时
        duration = (datetime.now() - start_time).total_seconds()
        
        # 9. 存入数据库（只保存元数据）
        record = DetectionRecord(
            file_name=video.filename or "video_detection",
            original_image="",
            result_image=output_video_url,
            mode="video",
            detections=json.dumps(all_detections[:100], ensure_ascii=False),
            target_count=total_targets,
            duration=duration,
            max_confidence=max([d["confidence"] for d in all_detections]) if all_detections else 0.0
        )
        db.add(record)
        db.commit()
        
        return {
            "code": 200,
            "message": f"视频检测完成，共处理 {processed_frames} 帧",
            "data": {
                "video_url": output_video_url,
                "record_id": record.id,
                "total_frames": processed_frames,
                "total_targets": total_targets,
                "duration": duration,
                "detections": all_detections[:200]  # 返回检测结果，最多200条
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"视频检测失败: {str(e)}"}
        )


# ==================== 历史记录接口 ====================
@app.get("/api/history/list")
async def get_history_list(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(DetectionRecord).order_by(DetectionRecord.created_at.desc())
    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for r in records:
        result.append({
            "id": r.id,
            "file_name": r.file_name,
            "file_path": r.original_image,
            "result_path": r.result_image,
            "mode": r.mode,
            "model_name": r.model_name,
            "detections": json.loads(r.detections) if r.detections else [],
            "target_count": r.target_count,
            "duration": r.duration,
            "max_confidence": r.max_confidence,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return {"code": 200, "data": {"total": total, "records": result}}


@app.get("/api/history/detail/{record_id}")
async def get_history_detail(record_id: int, db: Session = Depends(get_db)):
    record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    return {
        "code": 200,
        "data": {
            "id": record.id,
            "file_name": record.file_name,
            "file_path": record.original_image,
            "result_path": record.result_image,
            "mode": record.mode,
            "detections": json.loads(record.detections) if record.detections else [],
            "target_count": record.target_count,
            "duration": record.duration,
            "max_confidence": record.max_confidence,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    }


@app.delete("/api/history/{record_id}")
async def delete_history_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"code": 200, "message": "删除成功"}


@app.get("/api/history/stats")
async def get_history_stats(db: Session = Depends(get_db)):
    print("统计API被调用")
    try:
        records = db.query(DetectionRecord).all()
        total_count = len(records)
        
        total_targets = 0
        today_count = 0
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        for record in records:
            total_targets += record.target_count
            if str(record.created_at).startswith(today_str):
                today_count += 1
        
        result = {"code": 200, "data": {"total_count": total_count, "today_count": today_count, "total_targets": total_targets}}
        print(f"返回结果: {result}")
        return result
    except Exception as e:
        print(f"统计API错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"code": 500, "message": str(e)})


# ==================== 用户认证接口 ====================
class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


@app.post("/api/auth/register")
async def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={"code": 400, "message": "用户名已存在"}
            )

        hashed_password = get_password_hash(request.password)
        new_user = User(
            username=request.username,
            password=hashed_password,
            role="user"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "code": 200,
            "message": "注册成功",
            "data": {
                "id": new_user.id,
                "username": new_user.username,
                "role": new_user.role
            }
        }
    except Exception as e:
        import traceback
        print("注册错误:", str(e))
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"注册失败: {str(e)}"}
        )


@app.post("/api/auth/login")
async def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password):
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": "用户名或密码错误"}
        )

    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)