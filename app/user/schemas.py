from sqlmodel import SQLModel

class UserCreate(SQLModel):
    email: str
    username: str
    password: str

class UserRead(SQLModel):
    id: int
    email: str
    username: str