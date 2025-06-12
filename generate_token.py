import jwt
from datetime import datetime, timedelta, timezone

JWT_SECRET = "J1KnK0X_SyEJcd6ZhJVoX1Nhrrrrwwewwasd7u-NgPcD7U1ZmEd4"  # replace with your real secret
ALGORITHM = "HS256"

# Generate payload with timezone-aware datetime
payload = {
    "sub": "0002",  # or your custom user ID
    "role": "hr_user",     # optional - based on your auth system
    "exp": datetime.now(timezone.utc) + timedelta(hours=1),
}

# Generate JWT token
token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

print("JWT Token:\n", token)
