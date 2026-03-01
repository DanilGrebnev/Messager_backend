from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.auth.schemas import LoginRequest, TokenResponse
from app.auth.utils import JWTService
from app.database import SessionDep
from app.user.models import User
from app.user.utils import PasswordService

router = APIRouter(prefix="/auth", tags=["Auth"])
 
@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    session: SessionDep
):
    result = await session.execute(select(User).where(User.email == login_data.email))
    user = result.scalars().first()

    if user is None or not PasswordService.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    token = JWTService.create_access_token(user.id) # type: ignore
    return TokenResponse(access_token=token)