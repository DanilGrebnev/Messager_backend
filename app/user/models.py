from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    # Field используем, если для поля нужно указать дополнительные настройки
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    hashed_password: str