#!/usr/bin/env python3
"""
AI 聊天功能测试脚本
用于监测后端 AI 问答过程的运行情况
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.logger import get_logger
from app.config import settings

# 创建测试日志记录器
logger = get_logger("test_ai_chat", level="DEBUG")


def test_chat_api():
    """测试 AI 聊天 API"""
    test_start = datetime.now()
    logger.info("=" * 60)
    logger.info("AI 聊天功能测试开始")
    logger.info(f"测试时间: {test_start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        # 测试1: 配置检查
        logger.info("\n【测试1】配置检查")
        logger.info(f"DeepSeek API Key 配置状态: {'已配置' if settings.deepseek_api_key else '未配置'}")
        logger.info(f"DeepSeek API URL: {settings.deepseek_api_url}")

        if not settings.deepseek_api_key:
            logger.error("ERROR: DeepSeek API Key 未配置！")
            logger.error("请在 .env 文件中设置 DEEPSEEK_API_KEY")
            return False

        # 测试2: 导入检查
        logger.info("\n【测试2】导入检查")
        try:
            from app.api.chat import chat_completion, router
            logger.info("✓ chat.py 模块导入成功")
            logger.info(f"✓ 路由前缀: {router.prefix}")
            logger.info(f"✓ 路由标签: {router.tags}")
        except Exception as e:
            logger.error(f"✗ chat.py 模块导入失败: {e}")
            return False

        # 测试3: 请求测试
        logger.info("\n【测试3】API 请求测试")

        test_messages = [
            {"role": "user", "content": "什么是遥感目标检测？"},
            {"role": "assistant", "content": "遥感目标检测是利用计算机视觉技术从遥感影像中识别目标的过程。"},
            {"role": "user", "content": "支持检测哪些目标类型？"}
        ]

        request_data = {"messages": test_messages}
        logger.debug(f"测试请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

        # 模拟调用
        try:
            import asyncio
            result = asyncio.run(chat_completion(request_data))
            logger.info("✓ API 调用成功")
            logger.info(f"✓ 响应代码: {result.get('code')}")
            logger.info(f"✓ 请求ID: {result.get('data', {}).get('request_id')}")

            if result.get('code') == 200:
                content = result.get('data', {}).get('content', '')
                logger.info(f"✓ AI 回答长度: {len(content)} 字符")
                logger.debug(f"✓ AI 回答内容: {content[:200]}...")
            else:
                logger.warning(f"✗ API 返回错误: {result.get('message')}")

        except Exception as e:
            logger.error(f"✗ API 调用失败: {e}", exc_info=True)
            return False

        # 测试4: 网络连接测试
        logger.info("\n【测试4】网络连接测试")
        try:
            import requests
            response = requests.get("https://api.deepseek.com", timeout=10)
            logger.info(f"✓ DeepSeek API 可访问，状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠ DeepSeek API 访问异常: {e}")

        # 测试完成
        test_end = datetime.now()
        elapsed = (test_end - test_start).total_seconds()

        logger.info("\n" + "=" * 60)
        logger.info("AI 聊天功能测试完成")
        logger.info(f"测试耗时: {elapsed:.2f} 秒")
        logger.info(f"测试状态: ✅ 成功")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"测试过程发生异常: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_chat_api()
    sys.exit(0 if success else 1)