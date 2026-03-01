from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException
import jwt
from app.config import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import SessionDep
from app.user.models import User
from typing import Annotated

security = HTTPBearer()

class JWTService:
    @staticmethod
    def create_access_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }

        return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256") # type: ignore[reportUnknownMemberType]
    
    @staticmethod
    def decode_access_token(token: str) -> int | None:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"]) # type: ignore[reportUnknownMemberType]
            return int(payload["sub"])
        except(jwt.InvalidTokenError, KeyError, ValueError):
            return None

async def get_current_user(
    session: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    # берём user_id из access токена
    user_id = JWTService.decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
