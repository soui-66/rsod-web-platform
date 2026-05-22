#!/usr/bin/env python3
"""
统一日志模块
支持彩色终端输出，文件记录时自动去除颜色
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

try:
    from rich.logging import RichHandler

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from app.utils.paths import Paths
except ImportError:
    Paths = None


def setup_logging(
        level: str = "INFO",
        log_file: str = None,
        log_dir: str = None,
        name: str = None,
        use_colors: bool = True
):
    """
    统一日志配置
    """
    # 注意：这里用 %(asctime)s 会自动使用 default format
    log_format = "%(message)s"

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 清除已有的 handlers
    if logger.handlers:
        logger.handlers.clear()

    # 添加 Rich Handler（终端）- 自动处理颜色
    if RICH_AVAILABLE and use_colors:
        rich_handler = RichHandler(
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True
        )
        rich_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.addHandler(rich_handler)
    else:
        # 回退到普通 Handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        # 使用 %% 转义百分号
        formatter = logging.Formatter("%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # 添加文件 Handler - 不带颜色
    if log_file:
        if log_dir:
            log_path = Path(log_dir)
        elif Paths:
            log_path = Paths.logs()
        else:
            script_dir = Path(__file__).parent.parent.parent
            log_path = script_dir / "logs"

        log_path.mkdir(parents=True, exist_ok=True)
        log_file_path = log_path / log_file

        # 文件使用普通格式化器，不带颜色
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# ==================== 预定义配置 ====================

def setup_production_logging():
    return setup_logging(level="INFO", log_file="app.log")


def setup_debug_logging():
    return setup_logging(level="DEBUG", log_file="debug.log")


def setup_training_logging():
    return setup_logging(level="INFO", log_file="training.log")


def setup_converter_logging():
    return setup_logging(level="INFO", log_file="converter.log")


def setup_detect_logging():
    return setup_logging(level="INFO", log_file="detect.log")


def get_logger(name: str = None, level: str = "INFO"):
    return setup_logging(level=level, log_file=f"{name}.log" if name else None, name=name)


if __name__ == "__main__":
    logger = get_logger("test")
    logger.info("测试信息")
    logger.warning("测试警告")
    logger.error("测试错误")
    logger.debug("调试信息")