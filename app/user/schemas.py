from sqlmodel import SQLModel

class UserCreate(SQLModel):
    username: str
    email: str

class UserRead(SQLModel):
    id: int
    username: str
    email: str