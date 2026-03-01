from fastapi import FastAPI
from app.user.routers import router as user_router
from app.auth.routers import router as auth_router

app = FastAPI(title="Messager API")
app.include_router(user_router)
app.include_router(auth_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status":"ok"}