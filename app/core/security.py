from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt  # PyJWT
import bcrypt
import base64
from app.config import settings

try:
    from cryptography.fernet import Fernet
    _HAS_FERNET = True
except ImportError:
    _HAS_FERNET = False

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
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

# ── 密码哈希（bcrypt）────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# ── 字段级加密（AES-256，Fernet）────────────────────────────
class FieldEncryptor:
    def __init__(self):
        if _HAS_FERNET:
            raw_key  = bytes.fromhex(settings.FIELD_ENCRYPTION_KEY)
            fernet_key = base64.urlsafe_b64encode(raw_key)
            self.f = Fernet(fernet_key)
        else:
            self.f = None

    def encrypt(self, plaintext: str) -> str:
        if self.f:
            return self.f.encrypt(plaintext.encode()).decode()
        return plaintext  # fallback: no encryption

    def decrypt(self, ciphertext: str) -> str:
        if self.f:
            try:
                return self.f.decrypt(ciphertext.encode()).decode()
            except Exception:
                return ""
        return ciphertext  # fallback
