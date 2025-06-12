# app/auth.py

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.database import get_user_by_token
from app.config import JWT_SECRET, ALGORITHM

# FastAPI’s built-in HTTP Bearer token support
# HTTPBearer allows us to extract the Authorization Bearer token from the Authorization header
# security is an instance of HTTPBearer that we can use as a dependency
security = HTTPBearer()

# --- Decode JWT and extract payload ---

# function to decode JWT token and extract the username
# JWT_SECRET is the secret key used to sign the JWT
# ALGORITHM is the algorithm used to sign the JWT (e.g., HS256)
# payload is a dictionary that contains the decoded JWT payload
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

# function to get the current user based on the JWT token
# a JWT token has three parts: header, payload, and signature
# JWT payload contains the user information
# JWT header contains metadata about the token
# HTTPAuthorizationCredentials is a class that contains the credentials from the Authorization header
# credentials.credentials is the actual token string
# decode_jwt() decodes the JWT token and extracts the username
# get_user_by_token() retrieves the user information from Postgres database based on the username
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    username = decode_jwt(token)

    user_info = await get_user_by_token(username)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")

    return user_info
