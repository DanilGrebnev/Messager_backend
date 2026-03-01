from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DATABASE 
    POSTGRES_USER: str 
    POSTGRES_PASSWORD:str 
    POSTGRES_DB: str 
    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    # JWT
    JWT_SECRET: str

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"
        )
    
    model_config = {"env_file":".env", "extra":"ignore"}

settings = Settings() # type: ignore[call-arg]
