from fastapi import APIRouter, Depends, UploadFile, File, Form
from app.lesson.schema import LessonRequest, LessonResponse
from app.lesson.service import LessonService
from app.lesson.ai_service import LessonAiService
from app.shared.dependencies import SessionDep
from app.shared.schema import ApiResponse
import json

router = APIRouter(tags=["Aulas"])


def get_service(db: SessionDep) -> LessonService:
    return LessonService(db)


def get_ai_service(db: SessionDep) -> LessonAiService:
    return LessonAiService(db)


@router.post("/modules/{module_id}/lessons", response_model=ApiResponse, status_code=201)
async def criar(
    module_id: int,
    dados: str = Form(...),
    arquivo: UploadFile | None = File(default=None),
    service: LessonService = Depends(get_service),
):
    request = LessonRequest(**json.loads(dados))
    lesson = await service.criar(module_id, request, arquivo)
    return ApiResponse.ok("Aula criada com sucesso", LessonResponse.model_validate(lesson))


@router.get("/modules/{module_id}/lessons", response_model=ApiResponse)
async def listar(module_id: int, service: LessonService = Depends(get_service)):
    lessons = await service.listar_por_modulo(module_id)
    return ApiResponse.ok(dados=[LessonResponse.model_validate(l) for l in lessons])


@router.get("/lessons/{lesson_id}", response_model=ApiResponse)
async def buscar(lesson_id: int, service: LessonService = Depends(get_service)):
    lesson = await service.buscar_por_id(lesson_id)
    return ApiResponse.ok(dados=LessonResponse.model_validate(lesson))


@router.post("/lessons/{lesson_id}/gerar-conteudo", response_model=ApiResponse)
async def gerar_conteudo(lesson_id: int, ai_service: LessonAiService = Depends(get_ai_service)):
    result = await ai_service.gerar_conteudo(lesson_id)
    return ApiResponse.ok("Conteúdo enfileirado para geração via IA", result)


@router.get("/lessons/{lesson_id}/conteudo-pendente", response_model=ApiResponse)
async def conteudo_pendente(lesson_id: int, ai_service: LessonAiService = Depends(get_ai_service)):
    conteudo = await ai_service.buscar_conteudo_pendente(lesson_id)
    return ApiResponse.ok(dados=conteudo)


@router.post("/lessons/{lesson_id}/confirmar-conteudo", response_model=ApiResponse)
async def confirmar_conteudo(lesson_id: int, ai_service: LessonAiService = Depends(get_ai_service)):
    response = await ai_service.confirmar_conteudo(lesson_id)
    return ApiResponse.ok("Conteúdo confirmado e salvo", response)


@router.post("/lessons/{lesson_id}/regerar-conteudo", response_model=ApiResponse)
async def regerar_conteudo(lesson_id: int, ai_service: LessonAiService = Depends(get_ai_service)):
    result = await ai_service.gerar_conteudo(lesson_id)
    return ApiResponse.ok("Conteúdo regerado e enfileirado via IA", result)
