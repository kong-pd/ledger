"""
认证工具函数
============

两组能力：
  1. 密码：hash_password / verify_password（bcrypt）
  2. Token：create_access_token / get_current_user（JWT）

bcrypt 做了什么？
  注册时把明文密码变成一段不可逆的哈希存进数据库。
  登录时不是"解密比对"，而是把用户输入的密码再哈希一次，
  看结果跟数据库里存的是否一致。即使数据库泄露，攻击者也拿不到明文。

JWT 做了什么？
  登录成功后签发一个 token（一串编码过的字符串），里面藏了 user_id。
  之后每次请求，前端把 token 放在 Header 里发过来，
  后端解码验证就知道"这是谁"，不用每次都查密码。
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .database import get_db
from .models import User

# FastAPI 用这个从请求 Header 里提取 "Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ========== 密码 ==========

def hash_password(plain: str) -> str:
    """明文 → bcrypt 哈希"""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """验证明文是否匹配哈希"""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ========== JWT ==========

def create_access_token(user_id: int) -> str:
    """
    签发 token，payload 里放 user_id 和过期时间。
    过期后 jwt.decode 会自动抛 ExpiredSignatureError。
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI 依赖：从 token 解出 user_id，查库返回 User 对象。
    任何需要登录才能访问的路由，加上 user: User = Depends(get_current_user) 就行。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    return user
