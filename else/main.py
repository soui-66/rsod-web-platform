"""
遥感目标检测平台 - FastAPI 后端
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import  init_db
from app.api import detection, validation, history, auth, camera, model_api
from app.api.chat import router as chat_router

app = FastAPI(
    title="遥感目标智能检测平台",
    description="基于YOLO11的遥感图像目标检测系统API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# 静态文件CORS中间件
@app.middleware("http")
async def add_static_cors_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response


# 注册路由
app.include_router(detection.router)
app.include_router(validation.router)
app.include_router(history.router)
app.include_router(auth.router)
app.include_router(camera.router)
app.include_router(chat_router)
app.include_router(model_api.router)



@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ 数据库初始化完成")
    
    # 初始化 MinIO 服务
    try:
        from app.services.minio_service import minio_service
        print(f"✅ MinIO 服务初始化完成，可用状态: {minio_service.is_available()}")
    except Exception as e:
        print(f"❌ MinIO 服务初始化失败: {e}")


@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "healthy", "service": "rsod-web-platform", "version": "1.0.0"}


@app.get("/", tags=["根路径"])
async def root():
    return {"message": "欢迎使用遥感目标智能检测平台"}


@app.get("/test-minio", tags=["测试"])
async def test_minio():
    """测试 MinIO 上传功能"""
    try:
        from app.services.minio_service import minio_service
        
        # 测试上传
        test_data = b"test image data"
        url = minio_service.upload_image("test/test.jpg", test_data)
        
        # 列出所有文件
        files = minio_service.list_images()
        
        return {
            "status": "success",
            "message": "MinIO 上传测试成功",
            "uploaded_url": url,
            "files_in_bucket": files
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"MinIO 测试失败: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)