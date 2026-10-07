from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core import db
from app.core.config import settings
from app.core.errors import AppError
from app.routers import classify, clusters, health, jobs, kb, replies, sla, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.open_pool()
    yield
    db.close_pool()


app = FastAPI(title="ResolvIQ API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


app.include_router(health.router)
app.include_router(tickets.router, prefix="/api/v1")
app.include_router(kb.router, prefix="/api/v1")
app.include_router(classify.router, prefix="/api/v1")
app.include_router(replies.router, prefix="/api/v1")
app.include_router(sla.router, prefix="/api/v1")
app.include_router(clusters.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")