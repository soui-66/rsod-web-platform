from .detection import router as detection_router
from .validation import router as validation_router
from .history import router as history_router
from .auth import router as auth_router
from .camera import router as camera_router
from .model import router as model_router
from .video_detection import router as video_detection_router
from .categories import router as categories_router

# 导出路由供主应用使用
__all__ = ["detection", "validation", "history", "auth", "camera", "model", "video_detection", "categories"]

# 重新导出为模块属性
import sys
from . import detection
from . import validation
from . import history
from . import auth
from . import camera
from . import model
from . import video_detection
from . import categories

sys.modules[__name__].detection = detection
sys.modules[__name__].validation = validation
sys.modules[__name__].history = history
sys.modules[__name__].auth = auth
sys.modules[__name__].camera = camera
sys.modules[__name__].model = model
sys.modules[__name__].video_detection = video_detection
sys.modules[__name__].categories = categories
