"""
Security primitives:
- Argon2id password hashing
- JWT access/refresh token creation & verification
Never log or store plaintext passwords.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

# Argon2id is the default type for argon2-cffi's high level hasher
_hasher = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=2)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def create_token(subject: str, extra_claims: dict[str, Any], expires_minutes: int, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        **extra_claims,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, role: str, university_id: Optional[str]) -> str:
    return create_token(
        subject=user_id,
        extra_claims={"role": role, "university_id": university_id},
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_type="access",
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
