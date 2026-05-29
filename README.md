
# 遥感目标识别平台

基于YOLO11深度学习的多场景遥感影像目标检测系统，支持单图检测、批量检测、视频检测、实时检测等多种模式，提供模型管理、历史记录、AI智能问答等功能。

---

## 目录

- [项目概述](#项目概述)
- [技术架构](#技术架构)
- [项目结构详解](#项目结构详解)
- [核心功能原理](#核心功能原理)
- [数据准备与转换](#数据准备与转换)
- [模型训练](#模型训练)
- [技术栈](#技术栈)
- [数据库设计](#数据库设计)
- [部署运行](#部署运行)

---

## 项目概述

### 什么是遥感目标识别

遥感目标识别是利用计算机视觉和深度学习技术，自动从卫星或航拍遥感图像中检测和识别特定目标物体的过程。本平台支持飞机（aircraft）、油罐（oiltank）、立交桥（overpass）、操场（playground）等多类别的检测。

### 解决的问题

- **效率问题**：传统人工检测速度慢、成本高，无法处理海量遥感数据
- **实时性问题**：需要对视频流进行实时检测和分析
- **灵活性问题**：需要支持自定义模型的上传和切换
- **数据管理问题**：需要对检测历史、模型版本等进行有效管理

---

## 技术架构

### 整体架构

本平台采用前后端分离的架构设计：

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  智能检测    │  │  历史记录    │  │  AI问答      │  │
│  │  个人中心    │  │  模型管理    │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────┐
│                   后端 (FastAPI)                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  API路由层：认证、检测、历史、模型、问答、分类    │  │
│  ├──────────────────────────────────────────────────┤  │
│  │  服务层：检测服务、分类服务、MinIO服务           │  │
│  ├──────────────────────────────────────────────────┤  │
│  │  工具层：路径管理、日志、安全、验证               │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↕
┌──────────────────┐  ┌──────────────────┐
│  PostgreSQL      │  │  MinIO对象存储   │
│  关系型数据库     │  │  文件存储        │
└──────────────────┘  └──────────────────┘
```

### 架构特点

1. **前后端分离**：前端负责界面展示和用户交互，后端负责业务逻辑和数据处理
2. **模块化设计**：各功能模块独立，便于维护和扩展
3. **模型缓存**：支持多模型加载和缓存，避免重复加载
4. **实时通信**：使用WebSocket实现实时视频检测
5. **分层存储**：数据库存储元数据，MinIO存储文件

---

## 项目结构详解

```
rsod-web-platform/
├── backend/                          # 后端代码目录
│   ├── app/                          # 应用核心代码
│   │   ├── api/                      # API路由层
│   │   │   ├── auth.py              # 用户认证（登录/注册）
│   │   │   ├── detection.py         # 图像检测（单图/批量）
│   │   │   ├── video_detection.py   # 视频检测
│   │   │   ├── camera.py            # 摄像头实时检测
│   │   │   ├── history.py           # 历史记录
│   │   │   ├── model_api.py         # 模型管理（上传/删除）
│   │   │   ├── categories.py        # 目标类别管理
│   │   │   ├── chat.py              # AI智能问答
│   │   │   ├── validation.py        # 数据验证
│   │   │   └── init.py              # 初始化接口
│   │   ├── services/                 # 业务服务层
│   │   │   ├── detection_service.py  # 检测服务（核心推理逻辑）
│   │   │   ├── camera_detection_service.py  # 摄像头检测服务
│   │   │   ├── category_service.py   # 类别服务
│   │   │   └── minio_service.py      # MinIO对象存储服务
│   │   ├── utils/                    # 工具函数
│   │   │   ├── paths.py             # 路径管理
│   │   │   ├── logger.py            # 日志配置
│   │   │   ├── security.py          # 安全工具（密码哈希）
│   │   │   └── validation.py        # 数据验证
│   │   ├── models/                   # Pydantic模型
│   │   │   ├── init.py
│   │   │   └── schemas.py           # 请求/响应模型
│   │   ├── config.py                 # 配置文件
│   │   └── __init__.py
│   ├── convert/                      # 数据转换工具
│   │   ├── main.py                  # 转换主程序
│   │   ├── converter_voc.py         # VOC格式转YOLO
│   │   ├── detector.py              # 数据格式检测
│   │   └── validator.py             # 数据验证
│   ├── datasets/                     # 数据集目录
│   │   ├── rsod/                    # 原始RSOD数据集
│   │   └── converted/               # 转换后的YOLO格式数据集
│   ├── models/                       # 模型目录
│   │   └── yolo11n.pt               # YOLO11预训练模型
│   ├── runs/                         # 训练结果目录
│   │   └── detect/                  # 检测训练结果
│   │       ├── best_model.pt        # 最优模型（每次训练覆盖）
│   │       └── 2026_0522_1642/      # 某次训练的完整结果
│   ├── static/                       # 静态文件目录
│   │   └── results/                 # 检测结果
│   ├── main.py                       # FastAPI入口
│   ├── models.py                     # SQLAlchemy数据库模型
│   ├── database.py                   # 数据库连接
│   ├── init_db.py                    # 数据库初始化
│   ├── migrate_db.py                 # 数据库迁移
│   ├── setup_db.py                   # 数据库设置
│   ├── train.py                      # 模型训练脚本
│   ├── dataset.yaml                  # YOLO数据集配置
│   ├── requirements.txt              # Python依赖
│   ├── .env                          # 环境变量
│   └── env.example                   # 环境变量示例
├── frontend/                         # 前端代码目录
│   ├── src/
│   │   ├── views/                   # 页面组件
│   │   │   ├── Login.vue           # 登录页
│   │   │   ├── Register.vue        # 注册页
│   │   │   ├── Detection.vue       # 图像检测页
│   │   │   ├── Inference.vue       # 视频检测页
│   │   │   ├── History.vue         # 历史记录页
│   │   │   ├── Chat.vue            # AI问答页
│   │   │   └── Profile.vue         # 个人中心页
│   │   ├── components/              # 通用组件
│   │   │   ├── CameraDetection.vue  # 摄像头检测组件
│   │   │   ├── VideoDetection.vue   # 视频检测组件
│   │   │   ├── SliderCompare.vue    # 滑块对比组件
│   │   │   └── HelloWorld.vue
│   │   ├── api/                     # API调用
│   │   │   └── detection.js        # 检测接口
│   │   ├── router/                  # 路由
│   │   ├── App.vue                  # 主应用组件
│   │   └── main.js                  # 前端入口
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
├── scripts/                          # 辅助脚本
│   └── generate_ppt.py             # PPT生成脚本
├── docker-compose.yml                # Docker编排
└── README.md                         # 本文件
```

---

## 核心功能原理

### 1. 图像检测功能

#### 实现原理

图像检测基于YOLO11（You Only Look Once）深度学习模型：

1. **模型加载**：系统启动时或用户选择模型时，加载预训练的YOLO11模型
2. **图像预处理**：将上传的图像转换为模型输入格式（默认640x640）
3. **推理预测**：模型对图像进行前向传播，输出检测结果
4. **结果解析**：解析模型输出，提取目标类别、置信度和边界框
5. **置信度过滤**：根据用户设置的阈值过滤低置信度结果
6. **可视化**：在原图上绘制检测框和标签（绿色边框）
7. **结果保存**：将原图和结果图保存到MinIO或本地static目录
8. **数据库记录**：将检测记录写入数据库

#### 核心代码位置

- 检测服务：[backend/app/services/detection_service.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/app/services/detection_service.py)
- 检测API：[backend/app/api/detection.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/app/api/detection.py)

#### 置信度阈值

用户可通过前端滑块调整置信度阈值（默认0.25），系统会过滤掉低于阈值的检测结果，提高检测精度。

---

### 2. 视频检测功能

#### 实现原理

视频检测是对视频逐帧进行处理：

1. **视频保存**：将上传的视频保存到临时文件
2. **视频解码**：使用OpenCV读取视频文件，获取帧率、尺寸等信息
3. **逐帧检测**：
   - 读取视频每一帧
   - 将帧转换为JPEG格式
   - 使用YOLO模型进行检测
   - 在帧上绘制检测框
   - 将绘制后的帧写入输出视频
4. **结果合并**：统计所有帧的检测结果，计算总目标数量、最高置信度等
5. **视频生成**：使用OpenCV的VideoWriter将绘制后的帧重新编码为MP4视频
6. **清理临时文件**：删除临时视频文件

#### 性能优化

- 支持推理间隔设置（跳帧检测），减少计算量
- 模型缓存机制，避免重复加载
- 使用H.264编码压缩输出视频

#### 核心代码位置

- 视频检测服务：[backend/app/services/detection_service.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/app/services/detection_service.py) 中的 `detect_video()` 方法
- 视频检测API：[backend/app/api/video_detection.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/app/api/video_detection.py)

---

### 3. 实时视频检测功能

#### 实现原理

实时检测使用WebSocket实现前后端实时通信：

1. **连接建立**：前端切换到实时模式，点击"开始实时检测"，发起WebSocket连接
2. **视频播放**：用户播放视频
3. **帧捕获**：前端使用Canvas从视频元素中定时捕获当前帧
4. **帧传输**：将捕获的帧转换为Base64编码，通过WebSocket发送到后端
5. **实时推理**：后端接收帧数据，解码后立即进行YOLO检测
6. **结果推送**：检测结果（边界框、类别、置信度）通过WebSocket实时推送到前端
7. **画面叠加**：前端在视频画面上使用Canvas叠加显示检测框
8. **连接关闭**：视频暂停或结束时，关闭WebSocket连接

#### 技术细节

- 前端使用Canvas绘制检测框
- 后端逐帧处理，保持低延迟
- 支持播放、暂停控制
- 实时统计检测帧数和目标数

#### 核心代码位置

- WebSocket端点：[backend/app/api/detection.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/app/api/detection.py) 中的 `websocket_realtime_video()`
- 前端实时检测：[frontend/src/views/Inference.vue](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/frontend/src/views/Inference.vue)

---

### 4. 模型管理功能

#### 实现原理

模型管理支持用户上传和切换自定义模型：

1. **模型上传**：
   - 用户上传YOLO模型文件（.pt格式）
   - 输入模型名称和版本号
   - 将模型文件保存到指定目录
   - 将模型元数据（名称、版本、路径、上传时间）存入数据库

2. **模型列表**：
   - 从数据库查询所有模型
   - 返回给前端展示

3. **模型切换**：
   - 用户从下拉框选择模型
   - 前端将选中的模型ID发送给后端
   - 后端检查缓存中是否已加载该模型
   - 如已加载，直接使用；如未加载，从文件加载并存入缓存
   - 使用选中的模型进行后续检测

4. **模型删除**：
   - 从数据库删除模型记录
   - 从缓存中移除模型
   - （可选）删除模型文件

#### 模型缓存机制

使用Python字典实现模型缓存，键为模型ID或"default"（默认模型），值为包含模型实例和模型名称的字典。

```python
_detection_services = {
    "default": {
        "service": DetectionService("runs/detect/best_model.pt"),
        "model_name": "默认模型"
    },
    4: {
        "service": DetectionService("path/to/custom_model.pt"),
        "model_name": "我的模型"
    }
}
```

#### 模型切换流程

```
用户选择模型 → 查询数据库 → 检查缓存 → 加载/获取模型 → 用于检测
```

#### 核心代码位置

- 模型API：[backend/app/api/model_api.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/app/api/model_api.py)
- 模型加载：[backend/app/api/detection.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/app/api/detection.py) 中的 `get_detection_service()`

---

### 5. AI智能问答功能

#### 实现原理

AI问答结合数据库信息提供个性化回答：

1. **上下文构建**：
   - 从数据库获取用户的检测历史记录
   - 统计用户的检测次数、目标总数、常用类别等
   - 获取当前可用的模型列表
   - 获取目标类别信息

2. **提示词工程**：
   - 将上下文信息注入到AI提示词中
   - 构建包含用户数据、系统信息的完整提示词

3. **AI推理**：
   - 调用AI模型（如OpenAI API）生成回答
   - 将用户问题和提示词一起发送给AI

4. **结果保存**：
   - 将用户问题和AI回答保存到对话记录表

5. **结果返回**：
   - 将AI回答返回给前端展示

#### 个性化内容

- 用户检测统计数据（总检测数、总目标数等）
- 可用模型列表
- 目标类别信息
- 系统功能说明

#### 核心代码位置

- 聊天API：[backend/app/api/chat.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/app/api/chat.py)

---

### 6. 历史记录功能

#### 实现原理

历史记录功能用于查看和管理过去的检测记录：

1. **记录查询**：从数据库查询用户的检测记录，支持分页、按模式筛选
2. **记录详情**：展示单次检测的详细信息，包括原图、结果图、检测目标列表
3. **记录删除**：删除指定的检测记录
4. **结果导出**：导出检测结果

#### 核心代码位置

- 历史API：[backend/app/api/history.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/app/api/history.py)
- 前端页面：[frontend/src/views/History.vue](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/frontend/src/views/History.vue)

---

## 数据准备与转换

### RSOD数据集

本项目使用RSOD（Remote Sensing Object Detection）数据集，包含以下类别：
- aircraft（飞机）
- oiltank（油罐）
- overpass（立交桥）
- playground（操场）

数据集原始格式为PASCAL VOC格式。

### 数据格式转换

提供了数据转换工具，将VOC格式转换为YOLO格式：

#### 转换步骤

1. **数据准备**：将RSOD数据集放到 `backend/datasets/rsod/` 目录
2. **格式检测**：自动检测数据集格式（VOC/COCO/YOLO）
3. **数据转换**：
   - 将VOC的XML标注转换为YOLO的TXT格式
   - 按8:1:1比例划分为训练集、验证集、测试集
   - 生成类别映射
4. **生成配置**：自动生成 `dataset.yaml` 配置文件

#### 运行转换

```bash
cd backend/convert
python main.py
```

#### 转换后的目录结构

```
backend/datasets/converted/
├── aircraft/
│   ├── train/
│   │   ├── images/
│   │   └── labels/
│   ├── val/
│   └── test/
├── oiltank/
├── overpass/
└── playground/
```

#### 核心代码位置

- 转换主程序：[backend/convert/main.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/convert/main.py)
- VOC转换器：[backend/convert/converter_voc.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/convert/converter_voc.py)

---

## 模型训练

### 训练流程

1. **准备数据**：使用数据转换工具生成YOLO格式数据集和 `dataset.yaml`
2. **配置参数**：设置训练轮数、批次大小、学习率等参数
3. **开始训练**：加载预训练模型，开始训练
4. **监控训练**：查看训练指标（loss、mAP、precision、recall等）
5. **模型保存**：
   - 最优模型自动保存到 `runs/detect/best_model.pt`
   - 完整训练结果保存到 `runs/detect/{时间戳}/`

### 训练脚本

使用 [backend/train.py](file:///d:/Users/ZFF/PycharmProjects/rsod-web-platform/backend/train.py) 进行训练：

```bash
cd backend

# 使用默认参数训练
python train.py

# 自定义参数训练
python train.py --epochs 100 --batch 16 --imgsz 640 --device 0 --lr0 0.01
```

#### 训练参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--epochs` | 100 | 训练轮数 |
| `--batch` | 16 | 批次大小 |
| `--imgsz` | 640 | 输入图片尺寸 |
| `--device` | 0 | 训练设备（cpu/0/1） |
| `--lr0` | 0.01 | 初始学习率 |
| `--patience` | 20 | 早停耐心值（多少轮不提升就停止） |
| `--model` | yolo11n.pt | 预训练模型 |

### 训练输出

每次训练会在 `runs/detect/` 下生成一个时间戳命名的目录，包含：

```
runs/detect/2026_0522_1642/
├── best_model.pt          # 本次训练的最优模型（备份）
├── last_model.pt          # 本次训练的最终模型
├── args.yaml              # 训练参数记录
└── plots/                 # 训练指标图
    ├── confusion_matrix.png    # 混淆矩阵
    ├── F1_curve.png            # F1曲线
    ├── PR_curve.png            # Precision-Recall曲线
    ├── P_curve.png             # Precision曲线
    ├── R_curve.png             # Recall曲线
    ├── results.png             # 综合指标图
    ├── results.csv             # 指标数据
    ├── labels.jpg              # 标签统计
    ├── labels_correlogram.jpg  # 标签相关性
    ├── train_batch0.jpg        # 训练批次示例
    └── val_batch0_pred.jpg     # 验证结果示例
```

同时，最优模型会被复制到 `runs/detect/best_model.pt`，作为系统默认模型使用。

### 训练指标

- **mAP50**：IoU阈值为0.5时的平均精度
- **mAP50-95**：IoU阈值从0.5到0.95的平均精度
- **Precision**：精确率（检测正确的比例）
- **Recall**：召回率（找到的目标比例）
- **box_loss**：边界框损失
- **cls_loss**：分类损失

### 模型选择

训练完成后，系统会自动使用 `runs/detect/best_model.pt` 作为默认模型。用户也可以通过模型管理功能上传自己的模型。

---

## 技术栈

### 前端技术

- **Vue 3**：渐进式JavaScript框架，使用Composition API
- **Element Plus**：Vue 3组件库，提供丰富的UI组件
- **Vite**：下一代前端构建工具，提供快速的开发体验
- **Axios**：HTTP客户端，用于与后端API通信
- **WebSocket**：实时通信协议，用于实时视频检测

### 后端技术

- **FastAPI**：现代、快速的Python Web框架，自动生成API文档
- **SQLAlchemy**：Python SQL工具包和ORM，数据库交互
- **Pydantic**：数据验证和设置管理，API请求/响应验证
- **Ultralytics YOLO**：YOLO11模型的Python实现，目标检测
- **OpenCV**：计算机视觉库，图像处理和视频处理
- **Pillow**：Python图像处理库，图像绘制
- **MinIO**：高性能对象存储，图片和视频文件存储
- **PostgreSQL**：关系型数据库，数据持久化
- **python-pptx**：（可选）生成PPT文档

### 部署技术

- **Docker**：容器化平台
- **Docker Compose**：容器编排工具
- **Uvicorn**：ASGI服务器，运行FastAPI

---

## 数据库设计

### 核心数据表

#### 1. users（用户表）

存储用户基本信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String | 用户名（唯一） |
| hashed_password | String | 密码哈希 |
| role | String | 角色（user/admin） |
| created_at | DateTime | 创建时间 |

#### 2. detection_records（检测记录表）

存储每次检测的记录。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID（外键） |
| file_name | String | 文件名 |
| original_image | String | 原图URL |
| result_image | String | 结果图URL |
| mode | String | 检测模式（single/batch/video/camera） |
| model_name | String | 使用的模型名称 |
| detections | JSON | 检测结果JSON |
| target_count | Integer | 目标数量 |
| max_confidence | Float | 最高置信度 |
| duration | Float | 检测耗时（秒） |
| created_at | DateTime | 创建时间 |

#### 3. model_versions（模型版本表）

存储上传的模型信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 模型名称 |
| version | String | 版本号 |
| file_path | String | 模型文件路径 |
| uploaded_by | Integer | 上传用户ID（外键） |
| uploaded_at | DateTime | 上传时间 |

#### 4. target_categories（目标类别表）

存储目标类别信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 类别名称 |
| description | String | 描述 |
| color | String | 显示颜色 |
| count | Integer | 检测次数统计 |
| created_at | DateTime | 创建时间 |

#### 5. chat_records（对话记录表）

存储AI问答的历史记录。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID（外键） |
| question | String | 用户问题 |
| answer | String | AI回答 |
| created_at | DateTime | 创建时间 |

---

## 部署运行

### 环境要求

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- MinIO（可选，可使用本地文件存储）

### 快速开始

#### 1. 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
# 编辑 .env，配置数据库连接等

# 初始化数据库
python init_db.py

# 启动服务
uvicorn main:app --reload --port 8000
```

后端启动后，访问 http://localhost:8000/docs 查看API文档。

#### 2. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动后，访问 http://localhost:5173 。

#### 3. Docker部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 应用场景

- **农业监测**：虫害识别、作物长势分析、农田规划
- **城市规划**：建筑物识别、土地利用分析、城市扩张监测
- **海事监管**：船舶识别、航道监测、港口管理
- **航空管理**：机场飞机识别、流量统计
- **灾害监测**：灾后评估、目标搜救、损毁评估
- **环境保护**：污染监测、生态变化分析

---

## 技术亮点

1. **实时性**：WebSocket实时通信，低延迟检测，支持视频流实时检测
2. **准确性**：YOLO11深度学习模型，高准确率，支持自定义模型
3. **易用性**：简洁直观的用户界面，支持多种检测模式
4. **灵活性**：支持自定义模型上传和切换，模型缓存机制
5. **智能化**：AI问答，结合历史数据分析，提供个性化回答
6. **可扩展**：模块化架构，便于功能扩展和维护
7. **完整工具链**：提供数据转换、模型训练、推理部署全流程工具

---

## 许可证

MIT License

