from .detection import router as detection_router
from .validation import router as validation_router
from .history import router as history_router
from .auth import router as auth_router

__all__ = ["detection_router", "validation_router", "history_router", "auth_router"]