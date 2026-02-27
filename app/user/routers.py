from fastapi import APIRouter, HTTPException

from app.database import SessionDep
from app.user.models import User
from app.user.schemas import UserCreate, UserRead

router = APIRouter(prefix='/users', tags=['Users'])

@router.post("/", response_model=UserRead)
async def create_user(
    user_data: UserCreate,
    session: SessionDep
) -> User:
    user = User.model_validate(user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: SessionDep
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User")
    return user


