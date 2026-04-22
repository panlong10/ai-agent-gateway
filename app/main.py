from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.middleware.auth import AuthMiddleware
from app.middleware.ratelimit import RateLimitMiddleware
from app.routers import admin, health, proxy


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AI Agent Gateway",
    description="AI Agent 业务系统调用网关",
    version=get_settings().app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(health.router)
app.include_router(admin.router)
app.include_router(proxy.router)


@app.get("/")
async def root():
    return {"message": "AI Agent Gateway", "version": get_settings().app_version}
