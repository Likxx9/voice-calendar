from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from cryptography.fernet import Fernet
import base64
from app.config import settings

# ── JWT ──────────────────────────────────────────────────────
def create_access_token(user_id: uuid.UUID, role: str) -> str:
    """生成 JWT Access Token（60分钟有效）"""
    payload = {
        "sub":  str(user_id),
        "role": role,
        "type": "access",
        "iat":  datetime.now(tz=timezone.utc),
        "exp":  datetime.now(tz=timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: uuid.UUID) -> str:
    """生成 Refresh Token（30天有效）"""
    payload = {
        "sub":  str(user_id),
        "type": "refresh",
        "iat":  datetime.now(tz=timezone.utc),
        "exp":  datetime.now(tz=timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """验证 JWT Token，返回 payload 或 None"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

# ── 字段级加密（AES-256，Fernet）────────────────────────────
class FieldEncryptor:
    def __init__(self):
        # 从 32 字节十六进制密钥生成 Fernet key
        raw_key  = bytes.fromhex(settings.FIELD_ENCRYPTION_KEY)
        fernet_key = base64.urlsafe_b64encode(raw_key)
        self.f   = Fernet(fernet_key)

    def encrypt(self, plaintext: str) -> str:
        """加密字符串，返回 base64 密文"""
        return self.f.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """解密，失败返回空字符串"""
        try:
            return self.f.decrypt(ciphertext.encode()).decode()
        except Exception:
            return ""

# ── 密码哈希（用于本地账号，企业 SSO 场景可跳过）────────────
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
