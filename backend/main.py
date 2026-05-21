"""
遥感目标检测平台 - FastAPI 后端
"""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from ultralytics import YOLO
from passlib.context import CryptContext
import os
import uuid
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw

from database import get_db, init_db
from models import DetectionRecord, User

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
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)

model = YOLO("runs/detect/best_model.pt")


@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ 数据库初始化完成")


@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "healthy", "service": "rsod-web-platform", "version": "1.0.0"}


@app.get("/", tags=["根路径"])
async def root():
    return {"message": "欢迎使用遥感目标智能检测平台"}


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
    total_count = db.query(DetectionRecord).count()
    today = datetime.now().date()
    today_count = db.query(DetectionRecord).filter(
        DetectionRecord.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    total_targets = db.query(DetectionRecord).with_entities(
        db.func.sum(DetectionRecord.target_count)
    ).scalar() or 0

    return {"code": 200, "data": {"total_count": total_count, "today_count": today_count, "total_targets": total_targets}}


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