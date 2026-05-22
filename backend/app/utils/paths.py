#!/usr/bin/env python3
"""
路径管理模块
统一管理项目所有路径，支持从任意子模块定位项目根目录
"""

from pathlib import Path
from typing import Optional


def find_project_root(start_path=None, marker_file=".rsod_platform"):
    """
    从当前位置向上查找项目根目录（通过查找 marker file）

    核心算法：
    1. 从当前文件所在目录开始
    2. 逐级向上遍历父目录
    3. 找到 marker file 则停止，返回该目录

    参数：
        start_path: 起始查找路径，默认为调用此函数的文件所在目录
        marker_file: marker 文件名，用于区分不同项目

    返回：
        Path: 项目根目录路径

    异常：
        FileNotFoundError: 找不到 marker file
    """
    if start_path is None:
        import inspect
        frame = inspect.stack()[1]
        start_path = Path(frame.filename).parent

    current = Path(start_path).resolve()

    for parent in [current] + list(current.parents):
        marker_path = parent / marker_file
        if marker_path.exists():
            return parent

    raise FileNotFoundError(
        f"Could not find {marker_file} in {current} or any parent directory"
    )


class Paths:
    """
    项目路径管理类
    所有路径统一在此定义，避免硬编码
    """

    _root = None

    @classmethod
    def root(cls):
        """获取项目根目录"""
        if cls._root is None:
            cls._root = find_project_root()
        return cls._root

    @classmethod
    def backend(cls):
        """backend 目录"""
        return cls.root()  # 直接返回 root，不再加 /backend

    @classmethod
    def app(cls):
        """app 目录"""
        return cls.backend() / "app"

    @classmethod
    def datasets(cls):
        """数据集根目录"""
        return cls.backend() / "datasets"

    @classmethod
    def rsod_data(cls):
        """RSOD 数据集目录"""
        return cls.datasets() / "rsod"

    @classmethod
    def rsod_aircraft(cls):
        """RSOD aircraft 类别目录"""
        return cls.rsod_data() / "aircraft"

    @classmethod
    def rsod_oiltank(cls):
        """RSOD oiltank 类别目录"""
        return cls.rsod_data() / "oiltank"

    @classmethod
    def rsod_overpass(cls):
        """RSOD overpass 类别目录"""
        return cls.rsod_data() / "overpass"

    @classmethod
    def rsod_playground(cls):
        """RSOD playground 类别目录"""
        return cls.rsod_data() / "playground"

    @classmethod
    def rsod_train_images(cls):
        """RSOD 训练集图片目录"""
        return cls.rsod_data() / "train" / "images"

    @classmethod
    def rsod_train_labels(cls):
        """RSOD 训练集标注目录"""
        return cls.rsod_data() / "train" / "labels"

    @classmethod
    def rsod_test_images(cls):
        """RSOD 测试集图片目录"""
        return cls.rsod_data() / "test" / "images"

    @classmethod
    def rsod_test_labels(cls):
        """RSOD 测试集标注目录"""
        return cls.rsod_data() / "test" / "labels"

    @classmethod
    def static(cls):
        """静态资源目录（模型文件等）"""
        return cls.backend() / "static"

    @classmethod
    def models(cls):
        """模型文件目录"""
        return cls.backend() / "static"

    @classmethod
    def runs(cls):
        """运行时输出目录（检测结果、训练日志等）"""
        return cls.backend() / "runs"

    @classmethod
    def detect_results(cls):
        """检测结果目录"""
        return cls.runs() / "detect"

    @classmethod
    def logs(cls):
        """日志文件目录"""
        return cls.backend() / "logs"

    @classmethod
    def ensure_dir(cls, path):
        """
        确保目录存在，不存在则创建

        参数：
            path: 目录路径

        返回：
            Path: 确保存在的目录路径
        """
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def init_all_dirs(cls):
        """
        初始化所有必要的目录结构
        """
        dirs = [
            cls.datasets(),
            cls.rsod_data(),
            cls.runs(),
            cls.detect_results(),
            cls.logs(),
            cls.static(),
        ]
        for dir_path in dirs:
            cls.ensure_dir(dir_path)


# 便捷导出：常用路径的快捷访问
root = Paths.root()
backend_dir = Paths.backend()
app_dir = Paths.app()
datasets_dir = Paths.datasets()
