"""
Servicio de autenticación con JWT.
"""
from datetime import datetime, timedelta
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.user import User


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(user_id: UUID) -> str:
    """Crea un token JWT."""
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
    }
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """Decodifica un token JWT."""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Autentica un usuario por email y contraseña."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Obtiene un usuario por email."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Obtiene un usuario por ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str, full_name: str) -> User:
    """Crea un nuevo usuario."""
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
    )
    db.add(user)
    await db.flush()
    return user
