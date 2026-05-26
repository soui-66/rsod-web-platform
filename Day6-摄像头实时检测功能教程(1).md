# 摄像头实时检测功能实现教程

## 一、功能概述

摄像头实时检测功能是一个基于 **WebRTC + YOLO** 的实时目标检测系统，主要实现：

1. **前端**：通过浏览器获取摄像头视频流，实时捕获帧并发送到后端
2. **后端**：使用 YOLO 模型进行目标检测，返回检测结果
3. **实时交互**：前端在视频画面上绘制检测框，实现可视化效果

---

## 二、技术架构设计

### 2.1 架构选择原因

| 方案 | 说明 | 选择理由 |
|------|------|---------|
| **前端采集 + 后端检测** | 前端负责摄像头采集和渲染，后端负责模型推理 | 跨平台兼容、隐私保护、计算资源合理分配 |
| **纯前端检测** | 将模型下载到浏览器运行 | 隐私性好，但性能受限，模型加载慢 |
| **纯后端采集** | 后端直接访问摄像头 | 兼容性差，视频流传输压力大 |

**为什么选择前端采集 + 后端检测？**
- **兼容性**：前端使用标准 Web API，无需安装驱动
- **隐私保护**：视频流仅在前端处理，不传输完整视频
- **性能优化**：模型推理在后端高性能设备上运行
- **灵活性**：后端可部署在本地或云端

### 2.2 架构流程图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                               │
├─────────────────────────────────────────────────────────────────────┤
│  1. getUserMedia() 获取摄像头权限                                  │
│  2. <video> 元素显示实时画面                                       │
│  3. Canvas 绘制检测框覆盖层                                        │
│  4. requestAnimationFrame 循环截取画面                             │
│  5. Base64 编码后发送到后端                                        │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP POST /api/detection/camera/detect
                            │
┌─────────────────────────────────────────────────────────────────────┐
│                     后端 (FastAPI + YOLO)                         │
├─────────────────────────────────────────────────────────────────────┤
│  1. 接收 Base64 图像，解码为 NumPy 数组                            │
│  2. YOLO 模型推理检测目标                                          │
│  3. 解析检测结果（坐标、类别、置信度）                              │
│  4. 返回 JSON 格式的检测结果                                       │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            │ 返回检测框信息
                            │
┌─────────────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                               │
├─────────────────────────────────────────────────────────────────────┤
│  1. 接收检测框数据                                                 │
│  2. 在 Canvas 上绘制检测框和标签                                    │
│  3. 更新统计信息（帧率、总帧数、目标数）                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、前端实现详解

### 3.1 核心文件结构

```
frontend/src/
├── components/
│   └── CameraDetection.vue    # 摄像头检测主组件
├── api/
│   └── detection.js           # 检测相关 API 封装
└── utils/
    └── request.js             # HTTP 请求工具
```

### 3.2 摄像头权限获取

**为什么这样实现？**
- 使用 `getUserMedia` API 是 Web 标准方式，兼容性好
- 配置参数可指定分辨率和帧率，平衡质量与性能

```javascript
// frontend/src/components/CameraDetection.vue
const startLocalCamera = async () => {
  try {
    // 请求摄像头权限，配置视频参数
    videoStream = await navigator.mediaDevices.getUserMedia({
      video: {
        deviceId: cameraId.value !== 0 ? `device-id-${cameraId.value}` : undefined,
        width: { ideal: 640 },      // 理想宽度
        height: { ideal: 480 },     // 理想高度
        frameRate: { ideal: 30 },   // 理想帧率
      },
      audio: false,  // 不需要音频
    });

    // 将视频流绑定到 video 元素
    if (videoRef.value) {
      videoRef.value.srcObject = videoStream;
      videoRef.value.onloadedmetadata = () => {
        initCanvas();           // 初始化画布
        startDrawingLoop();     // 启动绘制循环
        startDetectionStream(); // 启动检测流
      };
    }
  } catch (error) {
    handleCameraError(error);
  }
};
```

### 3.3 错误处理机制

**为什么需要完善的错误处理？**
- 用户可能拒绝权限、设备不存在或被占用
- 提供友好的错误提示，提升用户体验

```javascript
// frontend/src/components/CameraDetection.vue
const handleCameraError = (error) => {
  console.error('摄像头错误:', error);
  
  // 根据错误类型给出针对性提示
  switch (error.name) {
    case 'NotAllowedError':
      ElMessage.error('摄像头权限被拒绝，请在浏览器设置中允许访问');
      break;
    case 'NotFoundError':
      ElMessage.error('未检测到摄像头设备，请检查设备连接');
      break;
    case 'NotReadableError':
      ElMessage.error('摄像头被其他应用占用，请关闭其他应用后重试');
      break;
    default:
      ElMessage.error('无法访问摄像头，请检查设备和权限设置');
  }

  cleanupResources();
  resetState();
};
```

### 3.4 实时帧捕获与检测

**为什么使用 requestAnimationFrame？**
- 与浏览器渲染同步，避免丢帧
- 自动适应浏览器刷新频率（通常 60fps）

```javascript
// frontend/src/components/CameraDetection.vue
const sendFrameForDetection = async () => {
  // 检测是否正在运行
  if (!isRunning.value) return;

  const currentTime = performance.now();
  // 根据推理间隔计算是否需要发送检测请求
  const timeSinceLastDetection = currentTime - lastDetectionTime;
  const targetInterval = (inferenceInterval.value * 1000) / 30;

  // 检查视频元素是否就绪
  if (!videoRef.value || !captureCanvasRef.value) {
    detectionFrameId = requestAnimationFrame(sendFrameForDetection);
    return;
  }

  // 非暂停状态且达到检测间隔时执行检测
  if (!isPaused.value && timeSinceLastDetection >= targetInterval) {
    try {
      const captureCanvas = captureCanvasRef.value;
      const ctx = captureCanvas.getContext('2d');
      // 从视频流截取当前帧
      ctx.drawImage(videoRef.value, 0, 0, captureCanvas.width, captureCanvas.height);
      
      // 转换为 Base64 编码（质量 0.7 平衡大小与质量）
      const imageData = captureCanvas.toDataURL('image/jpeg', 0.7);
      
      // 发送到后端检测
      const response = await detectFrame({ image: imageData });

      if (response.success) {
        // 更新检测结果
        currentBoxes.value = response.data.boxes || [];
        frameIndex.value = response.data.frame_index || frameIndex.value;
        fps.value = response.data.fps || fps.value;
        detectionTime.value = response.data.detection_time || 0;
        totalObjects.value = response.data.total_objects || 0;
        consecutiveErrorCount = 0;
        lastDetectionTime = currentTime;
      } else {
        handleDetectionError(response.message);
      }
    } catch (error) {
      handleDetectionError(error.message || '网络请求失败');
    }
  }

  // 继续下一帧循环
  detectionFrameId = requestAnimationFrame(sendFrameForDetection);
};
```

### 3.5 Canvas 绘制检测框

**为什么使用 Canvas 叠加？**
- 不修改原始视频流，保持视频流畅
- 支持透明叠加，检测框不会遮挡画面

```javascript
// frontend/src/components/CameraDetection.vue
const drawBoxes = () => {
  if (!canvasRef.value || !videoRef.value) return;

  const canvas = canvasRef.value;
  const ctx = canvas.getContext('2d');
  const video = videoRef.value;

  // 清除画布
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 计算缩放比例（处理视频与画布尺寸不一致）
  const scaleX = canvas.width / video.videoWidth;
  const scaleY = canvas.height / video.videoHeight;

  // 遍历所有检测框
  currentBoxes.value.forEach((box) => {
    // 转换坐标到画布坐标系
    const x1 = box.x1 * scaleX;
    const y1 = box.y1 * scaleY;
    const x2 = box.x2 * scaleX;
    const y2 = box.y2 * scaleY;
    const width = x2 - x1;
    const height = y2 - y1;

    // 绘制检测框边框
    ctx.strokeStyle = getBoxColor(box.class_name);
    ctx.lineWidth = 2;
    ctx.strokeRect(x1, y1, width, height);

    // 绘制半透明背景
    ctx.fillStyle = getBoxColor(box.class_name);
    ctx.globalAlpha = 0.1;
    ctx.fillRect(x1, y1, width, height);
    ctx.globalAlpha = 1;

    // 绘制标签（含类别名称和置信度）
    const label = `${box.chinese_name} ${(box.confidence * 100).toFixed(0)}%`;
    ctx.font = '12px Arial';
    ctx.fillStyle = getBoxColor(box.class_name);
    const labelWidth = ctx.measureText(label).width + 8;
    const labelHeight = 16;
    
    // 标签位置自适应（避免超出画面）
    if (y1 >= labelHeight) {
      ctx.fillRect(x1, y1 - labelHeight, labelWidth, labelHeight);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, x1 + 4, y1 - 4);
    } else {
      ctx.fillRect(x1, y1 + height, labelWidth, labelHeight);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, x1 + 4, y1 + height + 12);
    }
  });
};
```

### 3.6 API 封装

```javascript
// frontend/src/api/detection.js
export const detectFrame = (data) => {
  return request({
    url: '/detection/camera/detect',
    method: 'post',
    data,
  });
};
```

---

## 四、后端实现详解

### 4.1 核心文件结构

```
backend/app/
├── api/
│   └── camera.py          # 摄像头检测 API 路由
├── services/
│   ├── camera_detection_service.py  # 摄像头检测服务
│   └── detection_service.py        # 通用检测服务（YOLO模型）
└── config/
    └── settings.py        # 配置文件
```

### 4.2 API 路由设计

**为什么使用 FastAPI？**
- 高性能异步支持
- 自动生成 API 文档
- 类型提示支持，减少错误

```python
# backend/app/api/camera.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.camera_detection_service import camera_detection_service

router = APIRouter(prefix="/camera", tags=["camera"])

class StartDetectionRequest(BaseModel):
    """启动检测请求模型"""
    camera_id: int = Field(default=0, ge=0, description="摄像头设备ID")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="置信度阈值")
    iou_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="IOU阈值")
    inference_interval: int = Field(default=2, ge=1, description="推理间隔")

@router.post("/detect")
async def detect_frame(request: dict, current_user: User = Depends(get_current_user)):
    """
    接收前端发送的图像并返回检测结果
    
    请求体：
        image: base64编码的图像数据
    
    返回：
        检测结果（框坐标、类别、置信度）
    """
    try:
        if not camera_detection_service.is_running:
            return {"success": False, "message": "摄像头检测未启动"}
        
        # 获取图像数据
        image_data = request.get("image")
        if not image_data:
            return {"success": False, "message": "缺少图像数据"}
        
        # 解码 Base64 图像
        import base64
        import cv2
        import numpy as np
        
        # 移除 data:image 前缀
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        # Base64 解码
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return {"success": False, "message": "图像解码失败"}
        
        # 调用检测服务
        result = camera_detection_service.detect_image(image)
        
        return {
            "success": True,
            "message": "检测成功",
            "data": {
                "boxes": result.get("boxes", []),
                "frame_index": result.get("frame_index", 0),
                "fps": result.get("fps", 0),
                "detection_time": result.get("detection_time", 0),
                "total_objects": result.get("total_objects", 0)
            }
        }
    except Exception as e:
        logger.error(f"图像检测异常: {str(e)}")
        return {"success": False, "message": f"图像检测失败: {str(e)}"}
```

### 4.3 检测服务核心逻辑

**为什么使用单例模式？**
- 确保全局只有一个检测服务实例
- 避免重复加载模型，节省资源

```python
# backend/app/services/camera_detection_service.py

class CameraDetectionService:
    _instance: Optional['CameraDetectionService'] = None

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 检测状态
        self._status = DetectionStatus.STOPPED
        
        # 状态锁（线程安全）
        self._lock = threading.Lock()
        
        # 停止事件（用于控制线程退出）
        self._stop_event = threading.Event()
        
        # 暂停事件（用于控制暂停/恢复）
        self._pause_event = threading.Event()
        
        # 检测线程
        self._detection_thread = None
        
        # 检测配置
        self._confidence_threshold = 0.5
        self._iou_threshold = 0.7
        self._model_image_size = 320  # 降低分辨率提升速度
        
        # 并发控制信号量（最多5个并发请求）
        self._max_concurrent_requests = 5
        self._request_semaphore = threading.Semaphore(self._max_concurrent_requests)
        
        self._initialized = True

    def detect_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        检测单张图像（核心推理方法）
        
        参数：
            image: 输入图像（BGR格式）
        
        返回：
            Dict: 检测结果
        """
        # 使用信号量控制并发
        with self._request_semaphore:
            start_time = time.time()

            # 调用 YOLO 模型进行预测
            results = detection_service.model.predict(
                source=image,
                conf=self._confidence_threshold,  # 置信度阈值
                iou=self._iou_threshold,          # IOU 阈值
                save=False,                        # 不保存结果
                imgsz=self._model_image_size,      # 推理分辨率
                half=False,                        # FP16 推理（某些环境不支持）
                verbose=False,                     # 关闭详细输出
                stream=False                       # 非流式推理
            )

            # 解析检测结果
            boxes = []
            for result in results:
                for box in result.boxes:
                    # 获取检测框坐标（xyxy 格式）
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = detection_service.class_names.get(class_id, f"class_{class_id}")
                    chinese_name = detection_service.get_class_chinese_name(class_name)

                    boxes.append({
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "confidence": confidence,
                        "class_id": class_id,
                        "class_name": class_name,
                        "chinese_name": chinese_name
                    })

            detection_time = time.time() - start_time

            # 更新统计信息
            self._frame_count += 1
            self._fps_frame_count += 1
            current_time = time.time()
            elapsed = current_time - self._last_fps_time
            
            # 计算帧率（每秒更新一次）
            fps = 0.0
            if elapsed >= 1.0:
                fps = self._fps_frame_count / elapsed
                self._fps_frame_count = 0
                self._last_fps_time = current_time

            return {
                "boxes": boxes,
                "frame_index": self._frame_count,
                "fps": fps,
                "detection_time": detection_time,
                "total_objects": len(boxes)
            }
```

### 4.4 状态管理机制

**为什么需要完善的状态管理？**
- 避免重复启动检测
- 支持暂停/恢复功能
- 确保资源正确释放

```python
# backend/app/services/camera_detection_service.py
def start_detection(self, camera_id: int = 0, ...) -> bool:
    """启动摄像头实时检测"""
    # 如果已在运行，先停止再重新启动
    if self.is_running:
        logger.info("检测已在运行中，将先停止再重新启动")
        self.stop_detection()

    try:
        # 重置事件（确保可以重新启动）
        self._stop_event.clear()
        self._pause_event.clear()

        # 加载 YOLO 模型
        from ultralytics import YOLO
        detection_service.model = YOLO(settings.yolo_model_path)

        # 启动检测线程
        self._detection_thread = threading.Thread(
            target=self._detection_loop,
            daemon=True  # 守护线程，主线程退出时自动结束
        )
        self._detection_thread.start()

        self.status = DetectionStatus.RUNNING
        return True

    except Exception as e:
        logger.error(f"启动摄像头检测失败: {str(e)}")
        self.status = DetectionStatus.ERROR
        return False

def stop_detection(self):
    """停止摄像头检测"""
    if self.status == DetectionStatus.STOPPED:
        return

    # 设置停止事件（通知线程退出）
    self._stop_event.set()

    # 等待线程结束（最多等待3秒）
    if self._detection_thread is not None:
        self._detection_thread.join(timeout=3.0)
        self._detection_thread = None

    # 关闭帧源
    if self._frame_source is not None:
        self._frame_source.close()
        self._frame_source = None

    self.status = DetectionStatus.STOPPED
```

---

## 五、关键技术要点

### 5.1 WebRTC 视频流

```javascript
// 核心 API: frontend/src/components/CameraDetection.vue
navigator.mediaDevices.getUserMedia(constraints)
```

**参数说明**：
- `video.deviceId`：指定摄像头设备（多摄像头场景）
- `video.width/height`：理想分辨率
- `video.frameRate`：理想帧率

### 5.2 Base64 编码

```javascript
//frontend/src/components/CameraDetection.vue
canvas.toDataURL('image/jpeg', quality)
```

**质量参数**：
- `0.7`：平衡文件大小和图像质量
- 值越小文件越小，但图像越模糊

### 5.3 YOLO 模型推理

```python
#backend/app/services/camera_detection_service.py
results = model.predict(
    source=image,
    conf=0.5,      # 置信度阈值，低于此值的检测结果被过滤
    iou=0.7,       # IOU 阈值，用于非极大值抑制
    imgsz=320,     # 输入图像大小，越小速度越快
    half=False,    # 是否使用 FP16 推理
)
```

### 5.4 线程安全

```python
with self._lock:
    # 保护共享状态的读写操作
    self._current_result = result
```

**为什么需要锁？**
- 检测线程写入结果
- API 线程读取结果
- 防止数据竞争

---

## 六、性能优化策略

### 6.1 前端优化

| 优化项 | 实现方式 | 效果 |
|--------|---------|------|
| 帧跳过 | 每N帧检测一次 | 减少请求频率 |
| JPEG压缩 | quality=0.7 | 减小传输数据量 |
| requestAnimationFrame | 与渲染同步 | 避免丢帧 |

### 6.2 后端优化

| 优化项 | 实现方式 | 效果 |
|--------|---------|------|
| 降低分辨率 | imgsz=320 | 提升推理速度 |
| 并发控制 | Semaphore | 防止服务过载 |
| 异步处理 | 后台线程 | 不阻塞主线程 |

---

## 七、安全考虑

### 7.1 认证与授权

```python
#backend/app/api/camera.py
@router.post("/detect")
async def detect_frame(
    request: dict,
    current_user: User = Depends(get_current_user)  # 强制认证
):
    # 只有登录用户才能调用
```

### 7.2 输入验证

```python
#backend/app/api/camera.py
# Base64 解码前验证
if not image_data:
    return {"success": False, "message": "缺少图像数据"}

# 解码失败处理
image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
if image is None:
    return {"success": False, "message": "图像解码失败"}
```

### 7.3 资源限制

```python
#backend/app/api/camera.py
# 并发请求限制
self._max_concurrent_requests = 5
self._request_semaphore = threading.Semaphore(self._max_concurrent_requests)
```

---

## 八、常见问题与解决方案

### 8.1 摄像头无法打开

**问题**：`NotAllowedError` 或 `NotFoundError`

**解决方案**：
1. 检查浏览器权限设置
2. 确保摄像头设备已连接
3. 关闭其他占用摄像头的应用

### 8.2 检测框不动

**问题**：暂停恢复后检测框不更新

**解决方案**：
```javascript
// 确保暂停时循环继续运行
if (!isPaused.value) {
    // 执行检测逻辑
}
// 无论是否暂停，都继续循环
detectionFrameId = requestAnimationFrame(sendFrameForDetection);
```

### 8.3 帧率过低

**问题**：实时性差

**解决方案**：
1. 降低推理分辨率（imgsz=320）
2. 增加推理间隔（每2帧或3帧检测一次）
3. 降低图像质量（quality=0.7）

---

## 九、总结

摄像头实时检测功能的核心设计要点：

1. **架构选择**：前端采集 + 后端检测，兼顾兼容性和性能
2. **实时性**：使用 requestAnimationFrame 实现流畅循环
3. **线程安全**：使用锁和事件控制并发访问
4. **错误处理**：完善的错误捕获和用户提示
5. **性能优化**：帧跳过、图像压缩、并发控制

通过以上实现，可以构建一个稳定、高效的实时目标检测系统。
