from fastapi import APIRouter, Depends, Query
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

router = APIRouter(tags=["Quiz"])


def get_service(db: SessionDep) -> QuizService:
    return QuizService(db)


def get_ai_service(db: SessionDep) -> QuizAiService:
    return QuizAiService(db)


@router.post("/modules/{module_id}/quiz", response_model=ApiResponse, status_code=201)
def criar(module_id: int, request: QuizRequest, service: QuizService = Depends(get_service)):
    quiz = service.criar(module_id, request)
    return ApiResponse.ok("Quiz criado com sucesso", QuizResponse.model_validate(quiz))


@router.get("/modules/{module_id}/quiz", response_model=ApiResponse)
def buscar(module_id: int, service: QuizService = Depends(get_service)):
    quiz = service.buscar_por_modulo(module_id)
    return ApiResponse.ok(dados=QuizResponse.model_validate(quiz))


@router.post("/quiz/{quiz_id}", response_model=ApiResponse)
def configurar(quiz_id: int, request: QuizConfigRequest, service: QuizService = Depends(get_service)):
    quiz = service.configurar(quiz_id, request)
    return ApiResponse.ok("Quiz configurado com sucesso", QuizResponse.model_validate(quiz))


@router.post("/quiz/{quiz_id}/questions", response_model=ApiResponse, status_code=201)
def adicionar_pergunta(quiz_id: int, request: QuestionRequest, service: QuizService = Depends(get_service)):
    question = service.adicionar_pergunta(quiz_id, request)
    return ApiResponse.ok("Pergunta adicionada com sucesso", QuestionResponse.model_validate(question))


@router.get("/quiz/{quiz_id}/questions", response_model=ApiResponse)
def listar_perguntas(quiz_id: int, service: QuizService = Depends(get_service)):
    questions = service.listar_perguntas(quiz_id)
    return ApiResponse.ok(dados=[QuestionResponse.model_validate(q) for q in questions])


@router.post("/questions/{question_id}/alternatives", response_model=ApiResponse, status_code=201)
def adicionar_alternativa(question_id: int, request: AlternativeRequest, service: QuizService = Depends(get_service)):
    alt = service.adicionar_alternativa(question_id, request)
    return ApiResponse.ok("Alternativa adicionada com sucesso", AlternativeResponse.model_validate(alt))


@router.get("/questions/{question_id}/alternatives", response_model=ApiResponse)
def listar_alternativas(question_id: int, service: QuizService = Depends(get_service)):
    alts = service.listar_alternativas(question_id)
    return ApiResponse.ok(dados=[AlternativeResponse.model_validate(a) for a in alts])


@router.post("/modules/{module_id}/quiz/gerar", response_model=ApiResponse)
def gerar_quiz(
    module_id: int,
    quantidade: int = Query(default=5),
    ai_service: QuizAiService = Depends(get_ai_service),
):
    result = ai_service.gerar_quiz(module_id, quantidade)
    return ApiResponse.ok("Quiz gerado pela IA", result)


@router.get("/modules/{module_id}/quiz/pendente", response_model=ApiResponse)
def buscar_pendente(module_id: int, ai_service: QuizAiService = Depends(get_ai_service)):
    return ApiResponse.ok(dados=ai_service.buscar_pendente(module_id))


@router.post("/modules/{module_id}/quiz/confirmar", response_model=ApiResponse)
def confirmar_quiz(module_id: int, ai_service: QuizAiService = Depends(get_ai_service)):
    quiz = ai_service.confirmar_quiz(module_id)
    return ApiResponse.ok("Quiz confirmado e salvo com sucesso", QuizResponse.model_validate(quiz))


@router.post("/modules/{module_id}/quiz/regerar", response_model=ApiResponse)
def regerar_quiz(
    module_id: int,
    quantidade: int = Query(default=5),
    ai_service: QuizAiService = Depends(get_ai_service),
):
    result = ai_service.gerar_quiz(module_id, quantidade)
    return ApiResponse.ok("Quiz regerado pela IA", result)
