from fastapi import APIRouter, HTTPException

from app.auth.utils import CurrentUser
from app.database import SessionDep
from app.user.models import User
from app.user.schemas import UserCreate, UserRead
from app.user.utils import PasswordService

router = APIRouter(prefix='/users', tags=['Users'])

# Регистрация
@router.post("/registration", response_model=UserRead)
async def create_user(
    user_data: UserCreate,
    session: SessionDep,
):
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=PasswordService.hash_password(user_data.password)
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

# Получение пользователя по id
@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: SessionDep,
    # Данная конструкция позволяет сделать любой роут защищённым
    current_user: CurrentUser,
):
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User")
    return user


