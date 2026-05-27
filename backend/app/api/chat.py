# AI 聊天接口
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import requests
import json
from datetime import datetime
from app.config import settings
from app.utils.logger import get_logger
from database import get_db
from sqlalchemy.orm import Session
from models import ChatRecord

logger = get_logger("ai_chat", level="DEBUG")

router = APIRouter(prefix="/api/chat", tags=["AI 聊天"])


@router.post("/completion")
async def chat_completion(request: dict, db: Session = Depends(get_db)):
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=500, detail="DeepSeek API Key 未配置")

    messages = request.get("messages", [])
    user_id = request.get("user_id", 1)  # 获取用户ID，默认1

    # 保存用户消息到数据库
    for msg in messages:
        existing = db.query(ChatRecord).filter(
            ChatRecord.user_id == user_id,
            ChatRecord.role == msg["role"],
            ChatRecord.content == msg["content"]
        ).first()
        if not existing:
            db.add(ChatRecord(
                user_id=user_id,
                role=msg["role"],
                content=msg["content"]
            ))
    db.commit()

    system_prompt = {
        "role": "system",
        "content": """你是专业的遥感目标检测助手。

项目功能：
- 单张图像检测、批量图像检测、视频检测、摄像头实时检测
- 支持检测：飞机、油罐、操场、建筑物、船舶、农业虫害等目标
- 提供历史记录查看、导出、结果统计功能
- 使用 YOLO 模型，可调节置信度阈值

请简洁回答用户问题，不超过200字，仅回答遥感检测相关问题。"""
    }

    api_messages = [system_prompt] + messages

    try:
        response = requests.post(
            settings.deepseek_api_url,
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": api_messages,
                "temperature": 0.7,
                "max_tokens": 512
            },
            timeout=60
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        result = response.json()
        answer = result["choices"][0]["message"]["content"]

        # 保存 AI 回答到数据库
        db.add(ChatRecord(
            user_id=user_id,
            role="assistant",
            content=answer
        ))
        db.commit()

        return {
            "code": 200,
            "message": "success",
            "data": {
                "content": answer,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"AI 服务调用失败: {str(e)}"}
        )


@router.get("/history")
async def get_chat_history(user_id: int = 1, db: Session = Depends(get_db)):
    records = db.query(ChatRecord)\
        .filter(ChatRecord.user_id == user_id)\
        .order_by(ChatRecord.created_at.asc())\
        .all()

    history = []
    for r in records:
        history.append({
            "role": r.role,
            "content": r.content
        })

    return {"code": 200, "data": history}


@router.delete("/history")
async def clear_chat_history(user_id: int = 1, db: Session = Depends(get_db)):
    db.query(ChatRecord).filter(ChatRecord.user_id == user_id).delete()
    db.commit()
    return {"code": 200, "message": "清空成功"}


@router.get("/health")
async def chat_health():
    logger.info("AI 聊天健康检查")

    if not settings.deepseek_api_key:
        logger.warning("DeepSeek API Key 未配置")
        return {"status": "warning", "message": "DeepSeek API Key 未配置"}

    return {"status": "healthy", "message": "AI 聊天服务正常"}