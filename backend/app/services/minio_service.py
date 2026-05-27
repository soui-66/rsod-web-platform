"""
MinIO 对象存储服务
用于将检测图片上传到 MinIO 存储
"""
import os
import io
from minio import Minio
from minio.error import S3Error

from app.config import settings


class MinioService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MinioService, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance._available = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            self.client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure
            )
            
            # 确保 bucket 存在
            self._ensure_bucket()
            self._available = True
            print(f"[MinIO] 连接成功: {settings.minio_endpoint}")
        except Exception as e:
            print(f"[MinIO] 初始化失败: {e}")
            print("[MinIO] 请确保 MinIO 容器已启动，并在控制台中创建 Access Key")
            self.client = None
            self._available = False
        
        self._initialized = True

    def is_available(self):
        """检查 MinIO 服务是否可用"""
        return self._available

    def _ensure_bucket(self):
        """确保 bucket 存在，如果不存在则创建"""
        try:
            if not self.client.bucket_exists(settings.minio_bucket):
                self.client.make_bucket(settings.minio_bucket)
                print(f"[MinIO] Bucket '{settings.minio_bucket}' 创建成功")
            else:
                print(f"[MinIO] Bucket '{settings.minio_bucket}' 已存在")
        except S3Error as e:
            print(f"[MinIO] Bucket 操作失败: {e}")
            self._available = False

    def upload_image(self, file_name: str, image_data: bytes, content_type: str = "image/jpeg") -> str:
        """
        上传图片到 MinIO
        
        参数:
            file_name: 存储的文件名
            image_data: 图片二进制数据
            content_type: 内容类型
        
        返回:
            文件访问 URL
        """
        try:
            # 使用 BytesIO 包装二进制数据
            data = io.BytesIO(image_data)
            data_length = len(image_data)
            
            # 上传文件
            self.client.put_object(
                settings.minio_bucket,
                file_name,
                data,
                data_length,
                content_type=content_type
            )
            
            # 生成访问 URL
            url = f"http://{settings.minio_endpoint}/{settings.minio_bucket}/{file_name}"
            print(f"[MinIO] 文件上传成功: {url}")
            return url
            
        except S3Error as e:
            print(f"[MinIO] 文件上传失败: {e}")
            raise

    def download_image(self, file_name: str) -> bytes:
        """
        从 MinIO 下载图片
        
        参数:
            file_name: 存储的文件名
        
        返回:
            图片二进制数据
        """
        try:
            response = self.client.get_object(settings.minio_bucket, file_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            print(f"[MinIO] 文件下载失败: {e}")
            raise

    def delete_image(self, file_name: str) -> bool:
        """
        删除 MinIO 中的图片
        
        参数:
            file_name: 存储的文件名
        
        返回:
            是否删除成功
        """
        try:
            self.client.remove_object(settings.minio_bucket, file_name)
            print(f"[MinIO] 文件删除成功: {file_name}")
            return True
        except S3Error as e:
            print(f"[MinIO] 文件删除失败: {e}")
            return False

    def list_images(self) -> list:
        """列出 MinIO bucket 中的所有文件"""
        try:
            objects = self.client.list_objects(settings.minio_bucket)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"[MinIO] 列出文件失败: {e}")
            return []


# 全局实例
minio_service = MinioService()
