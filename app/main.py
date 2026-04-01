from contextlib import asynccontextmanager
from fastapi import FastAPI
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="PoC LLM UFC Simples — Python",
    description="Plataforma LMS com IA embarcada usando FastAPI",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_exception_handler(RecursoNaoEncontradoException, recurso_nao_encontrado_handler)
app.add_exception_handler(RegraDeNegocioException, regra_de_negocio_handler)
app.add_exception_handler(Exception, erro_interno_handler)

app.include_router(course_router)
app.include_router(module_router)
app.include_router(lesson_router)
app.include_router(quiz_router)
