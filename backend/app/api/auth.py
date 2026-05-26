# 用户认证接口
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import User
from app.utils.security import verify_password, get_password_hash

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册接口

    参数：
        username: 用户名
        password: 密码

    返回：
        注册结果，包含用户ID、用户名、角色
    """
    try:
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={"code": 400, "message": "用户名已存在"}
            )

        hashed_password = get_password_hash(request.password)
        new_user = User(
            username=request.username,
            password=hashed_password,
            role="user"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "code": 200,
            "message": "注册成功",
            "data": {
                "id": new_user.id,
                "username": new_user.username,
                "role": new_user.role
            }
        }
    except Exception as e:
        import traceback
        print("注册错误:", str(e))
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"注册失败: {str(e)}"}
        )


@router.post("/login")
async def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录接口

    参数：
        username: 用户名
        password: 密码

    返回：
        登录结果，包含用户ID、用户名、角色
    """
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password):
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": "用户名或密码错误"}
        )

    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    }