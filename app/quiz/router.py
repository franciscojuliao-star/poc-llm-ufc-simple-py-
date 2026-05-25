from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from app.quiz.schema import (
    QuizRequest, QuizResponse, QuizConfigRequest,
    QuestionRequest, QuestionResponse,
    AlternativeRequest, AlternativeResponse,
    QuizGeneratedResponse,
)
from app.quiz.service import QuizService
from app.quiz.ai_service import QuizAiService
from app.shared.dependencies import SessionDep
from app.shared.schema import ApiResponse
from app.shared.cache import cache_get, cache_set, cache_delete, serialize

router = APIRouter(tags=["Quiz"])


def _key_quiz(module_id: int) -> str:
    return f"quiz:module:{module_id}"


def get_service(db: SessionDep) -> QuizService:
    return QuizService(db)


def get_ai_service(db: SessionDep) -> QuizAiService:
    return QuizAiService(db)


@router.post("/modules/{module_id}/quiz", response_model=ApiResponse, status_code=201)
async def criar(module_id: int, request: QuizRequest, service: QuizService = Depends(get_service)):
    quiz = await service.criar(module_id, request)
    await cache_delete(_key_quiz(module_id))
    return ApiResponse.ok("Quiz criado com sucesso", QuizResponse.model_validate(quiz))


@router.get("/modules/{module_id}/quiz", response_model=ApiResponse)
async def buscar(module_id: int, service: QuizService = Depends(get_service)):
    key = _key_quiz(module_id)
    cached = await cache_get(key)
    if cached is not None:
        return Response(content=cached, media_type="application/json")
    quiz = await service.buscar_por_modulo(module_id)
    body = serialize(ApiResponse.ok(dados=QuizResponse.model_validate(quiz)).model_dump(mode="json"))
    await cache_set(key, body)
    return Response(content=body, media_type="application/json")


@router.post("/quiz/{quiz_id}", response_model=ApiResponse)
async def configurar(quiz_id: int, request: QuizConfigRequest, service: QuizService = Depends(get_service)):
    quiz = await service.configurar(quiz_id, request)
    return ApiResponse.ok("Quiz configurado com sucesso", QuizResponse.model_validate(quiz))


@router.post("/quiz/{quiz_id}/questions", response_model=ApiResponse, status_code=201)
async def adicionar_pergunta(quiz_id: int, request: QuestionRequest, service: QuizService = Depends(get_service)):
    question = await service.adicionar_pergunta(quiz_id, request)
    return ApiResponse.ok("Pergunta adicionada com sucesso", QuestionResponse.model_validate(question))


@router.get("/quiz/{quiz_id}/questions", response_model=ApiResponse)
async def listar_perguntas(quiz_id: int, service: QuizService = Depends(get_service)):
    questions = await service.listar_perguntas(quiz_id)
    return ApiResponse.ok(dados=[QuestionResponse.model_validate(q) for q in questions])


@router.post("/questions/{question_id}/alternatives", response_model=ApiResponse, status_code=201)
async def adicionar_alternativa(question_id: int, request: AlternativeRequest, service: QuizService = Depends(get_service)):
    alt = await service.adicionar_alternativa(question_id, request)
    return ApiResponse.ok("Alternativa adicionada com sucesso", AlternativeResponse.model_validate(alt))


@router.get("/questions/{question_id}/alternatives", response_model=ApiResponse)
async def listar_alternativas(question_id: int, service: QuizService = Depends(get_service)):
    alts = await service.listar_alternativas(question_id)
    return ApiResponse.ok(dados=[AlternativeResponse.model_validate(a) for a in alts])


@router.post("/modules/{module_id}/quiz/gerar", response_model=ApiResponse)
async def gerar_quiz(
    module_id: int,
    quantidade: int = Query(default=5),
    ai_service: QuizAiService = Depends(get_ai_service),
):
    result = await ai_service.gerar_quiz(module_id, quantidade)
    return ApiResponse.ok("Quiz enfileirado para geração via IA", result)


@router.get("/modules/{module_id}/quiz/pendente", response_model=ApiResponse)
async def buscar_pendente(module_id: int, ai_service: QuizAiService = Depends(get_ai_service)):
    quiz = await ai_service.buscar_pendente(module_id)
    return ApiResponse.ok(dados=quiz)


@router.post("/modules/{module_id}/quiz/confirmar", response_model=ApiResponse)
async def confirmar_quiz(module_id: int, ai_service: QuizAiService = Depends(get_ai_service)):
    quiz = await ai_service.confirmar_quiz(module_id)
    await cache_delete(_key_quiz(module_id))
    return ApiResponse.ok("Quiz confirmado e salvo com sucesso", QuizResponse.model_validate(quiz))


@router.post("/modules/{module_id}/quiz/regerar", response_model=ApiResponse)
async def regerar_quiz(
    module_id: int,
    quantidade: int = Query(default=5),
    ai_service: QuizAiService = Depends(get_ai_service),
):
    result = await ai_service.gerar_quiz(module_id, quantidade)
    return ApiResponse.ok("Quiz regerado e enfileirado via IA", result)
