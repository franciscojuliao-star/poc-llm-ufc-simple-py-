import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from app.core.config import settings
from app.course.router import router as course_router
from app.module.router import router as module_router
from app.lesson.router import router as lesson_router
from app.quiz.router import router as quiz_router
from app.shared.exception import (
    RecursoNaoEncontradoException,
    RegraDeNegocioException,
    recurso_nao_encontrado_handler,
    regra_de_negocio_handler,
    erro_interno_handler,
)
from app.shared.redis_client import get_async_redis, close_async_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    for subdir in ("courses", "modules", "lessons"):
        os.makedirs(os.path.join(settings.UPLOAD_DIR, subdir), exist_ok=True)
    redis = await get_async_redis()
    await redis.ping()
    yield
    await close_async_redis()


app = FastAPI(
    title="PoC LLM UFC Simples — Python",
    description="Plataforma LMS com IA embarcada usando FastAPI async + Celery + Redis",
    version="0.2.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_exception_handler(RecursoNaoEncontradoException, recurso_nao_encontrado_handler)
app.add_exception_handler(RegraDeNegocioException, regra_de_negocio_handler)
app.add_exception_handler(Exception, erro_interno_handler)

app.include_router(course_router)
app.include_router(module_router)
app.include_router(lesson_router)
app.include_router(quiz_router)
