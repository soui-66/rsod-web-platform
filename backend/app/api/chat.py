# AI 聊天接口
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import requests
import json
from datetime import datetime, timedelta
from app.config import settings
from app.utils.logger import get_logger
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import ChatRecord, DetectionRecord, ModelVersion, TargetCategory

logger = get_logger("ai_chat", level="DEBUG")

router = APIRouter(prefix="/api/chat", tags=["AI 聊天"])


def get_user_context(user_id: int, db: Session) -> dict:
    """获取用户相关的上下文信息"""

    # 1. 获取用户检测统计
    total_detections = db.query(DetectionRecord).filter(
        DetectionRecord.user_id == user_id
    ).count()

    # 2. 获取最近7天的检测次数
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_week_detections = db.query(DetectionRecord).filter(
        DetectionRecord.user_id == user_id,
        DetectionRecord.created_at >= seven_days_ago
    ).count()

    # 3. 获取最近5条检测记录
    recent_records = db.query(DetectionRecord).filter(
        DetectionRecord.user_id == user_id
    ).order_by(DetectionRecord.created_at.desc()).limit(5).all()

    # 4. 获取可用模型列表
    models = db.query(ModelVersion).filter(
        ModelVersion.is_active == True
    ).all()

    # 5. 获取目标类别统计（全局，不按用户）
    categories = db.query(TargetCategory).order_by(
        TargetCategory.count.desc()
    ).limit(10).all()

    # 6. 获取用户最常用的检测模式
    mode_stats = db.query(
        DetectionRecord.mode,
        func.count(DetectionRecord.id).label('count')
    ).filter(
        DetectionRecord.user_id == user_id
    ).group_by(DetectionRecord.mode).all()

    # 7. 计算平均检测目标数
    avg_targets = db.query(
        func.avg(DetectionRecord.target_count)
    ).filter(
        DetectionRecord.user_id == user_id
    ).scalar() or 0

    return {
        "total_detections": total_detections,
        "recent_week_detections": recent_week_detections,
        "recent_records": recent_records,
        "models": models,
        "categories": categories,
        "mode_stats": mode_stats,
        "avg_targets": round(float(avg_targets), 1)
    }


def build_system_prompt(user_id: int, db: Session) -> str:
    """动态构建系统提示词"""
    context = get_user_context(user_id, db)

    # 构建模型列表
    if context["models"]:
        model_info = "\n".join([
            f"  - {m.name} (v{m.version}): {m.description or '自定义模型'}"
            for m in context["models"]
        ])
    else:
        model_info = "  - 默认模型 (YOLO11)"

    # 构建类别统计
    if context["categories"]:
        category_info = "\n".join([
            f"  - {c.name}: {c.count} 次"
            for c in context["categories"]
        ])
    else:
        category_info = "  - 暂无统计数据"

    # 构建最近检测记录
    if context["recent_records"]:
        recent_info = "\n".join([
            f"  - [{r.created_at.strftime('%m-%d %H:%M')}] {r.file_name}: 检测到 {r.target_count} 个目标 ({r.mode}模式)"
            for r in context["recent_records"]
        ])
    else:
        recent_info = "  - 暂无检测记录"

    # 构建检测模式统计
    if context["mode_stats"]:
        mode_info = "\n".join([
            f"  - {m.mode}: {m.count} 次"
            for m in context["mode_stats"]
        ])
    else:
        mode_info = "  - 暂无数据"

    return f"""你是专业的遥感目标检测助手，负责帮助用户使用遥感图像目标检测平台。

## 平台功能介绍
- 单张图像检测：上传单张图片进行目标检测
- 批量图像检测：一次上传多张图片批量检测
- 视频检测：对视频文件进行逐帧检测
- 摄像头实时检测：使用摄像头进行实时目标检测
- 支持检测目标：飞机、油罐、操场、建筑物、船舶、农业虫害等
- 使用 YOLO 模型，可调节置信度阈值

## 当前用户数据
【检测统计】
- 总检测次数：{context["total_detections"]} 次
- 近7天检测：{context["recent_week_detections"]} 次
- 平均每张检测到：{context["avg_targets"]} 个目标

【检测模式偏好】
{mode_info}

【最近检测记录】
{recent_info}

【可用模型】
{model_info}

【平台目标统计（全部用户）】
{category_info}

## 回答要求
1. 根据用户的检测历史提供个性化建议
2. 如果用户问检测相关问题，结合其历史数据回答
3. 推荐合适的模型或检测参数
4. 回答简洁专业，不超过300字
5. 如果用户问的问题与遥感检测无关，礼貌引导回检测话题"""


@router.post("/completion")
async def chat_completion(request: dict, db: Session = Depends(get_db)):
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=500, detail="DeepSeek API Key 未配置")

    messages = request.get("messages", [])
    user_id = request.get("user_id", 1)

    # 保存用户消息到数据库
    for msg in messages:
        if msg["role"] == "user":
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

    # 动态构建系统提示词（包含用户数据）
    system_content = build_system_prompt(user_id, db)
    system_prompt = {
        "role": "system",
        "content": system_content
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
                "max_tokens": 800
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
    records = db.query(ChatRecord) \
        .filter(ChatRecord.user_id == user_id) \
        .order_by(ChatRecord.created_at.asc()) \
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