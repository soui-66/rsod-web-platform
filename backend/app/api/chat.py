# AI 聊天接口 - 带详细日志记录
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import requests
from datetime import datetime
from app.config import settings
from app.utils.logger import get_logger

# 创建专门的日志记录器
logger = get_logger("ai_chat", level="DEBUG")

router = APIRouter(prefix="/api/chat", tags=["AI 聊天"])


@router.post("/completion")
async def chat_completion(request: dict):
    """
    AI 聊天完成接口
    调用 DeepSeek API 进行对话
    """
    request_id = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

    try:
        # ========== 日志：请求开始 ==========
        logger.info(f"[REQUEST-{request_id}] AI 聊天请求开始")
        logger.debug(f"[REQUEST-{request_id}] 请求体: {request}")

        # ========== 日志：配置检查 ==========
        if not settings.deepseek_api_key:
            logger.error(f"[REQUEST-{request_id}] DeepSeek API Key 未配置")
            raise HTTPException(status_code=500, detail="DeepSeek API Key 未配置")

        logger.info(f"[REQUEST-{request_id}] DeepSeek API Key 已配置")

        # ========== 日志：参数提取 ==========
        messages = request.get("messages", [])
        logger.info(f"[REQUEST-{request_id}] 消息数量: {len(messages)}")

        if messages:
            last_message = messages[-1] if messages else {}
            logger.debug(f"[REQUEST-{request_id}] 最后一条消息: {last_message.get('content', '')[:100]}...")

        # ========== 日志：构建请求 ==========
        system_prompt = {
            "role": "system",
            "content": """你是一个专业的遥感目标检测助手。请回答用户关于遥感目标检测的问题。"""
        }
        api_messages = [system_prompt] + messages

        logger.info(f"[REQUEST-{request_id}] 正在调用 DeepSeek API")
        logger.debug(f"[REQUEST-{request_id}] API URL: {settings.deepseek_api_url}")

        # ========== 日志：发送请求 ==========
        start_time = datetime.now()
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
                "max_tokens": 2048
            },
            timeout=60
        )
        elapsed_time = (datetime.now() - start_time).total_seconds() * 1000

        # ========== 日志：响应处理 ==========
        logger.info(f"[REQUEST-{request_id}] API 响应状态码: {response.status_code}")
        logger.info(f"[REQUEST-{request_id}] API 响应耗时: {elapsed_time:.2f}ms")

        if response.status_code != 200:
            logger.error(f"[REQUEST-{request_id}] API 调用失败: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        # ========== 日志：解析响应 ==========
        result = response.json()
        answer = result["choices"][0]["message"]["content"]

        logger.debug(f"[REQUEST-{request_id}] 响应数据: {result}")
        logger.info(f"[REQUEST-{request_id}] AI 回答长度: {len(answer)} 字符")

        # ========== 日志：请求完成 ==========
        logger.info(f"[REQUEST-{request_id}] AI 聊天请求完成")

        return {
            "code": 200,
            "message": "success",
            "data": {
                "content": answer,
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id
            }
        }

    except HTTPException as e:
        # 已知异常
        logger.error(f"[REQUEST-{request_id}] HTTP 异常: {e.detail}")
        raise

    except requests.exceptions.Timeout:
        logger.error(f"[REQUEST-{request_id}] 请求超时")
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "请求超时", "request_id": request_id}
        )

    except requests.exceptions.ConnectionError:
        logger.error(f"[REQUEST-{request_id}] 网络连接错误")
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "网络连接错误", "request_id": request_id}
        )

    except Exception as e:
        # 未知异常
        logger.error(f"[REQUEST-{request_id}] 未知异常: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"AI 服务调用失败: {str(e)}", "request_id": request_id}
        )


@router.get("/health")
async def chat_health():
    """检查 AI 聊天服务健康状态"""
    logger.info("AI 聊天健康检查")

    if not settings.deepseek_api_key:
        logger.warning("DeepSeek API Key 未配置")
        return {"status": "warning", "message": "DeepSeek API Key 未配置"}

    return {"status": "healthy", "message": "AI 聊天服务正常"}