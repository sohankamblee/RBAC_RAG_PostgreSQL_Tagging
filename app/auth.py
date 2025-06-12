# app/auth.py

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.database import get_user_by_token
from app.config import JWT_SECRET, ALGORITHM

# FastAPI’s built-in HTTP Bearer token support
security = HTTPBearer()

# --- Decode JWT and extract payload ---
def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid JWT payload")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# --- Dependency for protected routes ---
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    username = decode_jwt(token)

    user_info = await get_user_by_token(username)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")

    return user_info
