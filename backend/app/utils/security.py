# 安全工具
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], default="pbkdf2_sha256", deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)