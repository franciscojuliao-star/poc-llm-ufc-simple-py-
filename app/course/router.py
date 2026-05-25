from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from fastapi.responses import Response
from app.course.schema import CourseRequest, CourseUpdateRequest, CourseResponse
from app.course.service import CourseService
from app.shared.dependencies import SessionDep
from app.shared.schema import ApiResponse
from app.shared.cache import cache_get, cache_set, cache_delete, serialize

router = APIRouter(prefix="/courses", tags=["Cursos"])

PER_PAGE = 20


def _key_page(page: int) -> str:
    return f"courses:p{page}"


def _key_one(course_id: int) -> str:
    return f"course:{course_id}"


def get_service(db: SessionDep) -> CourseService:
    return CourseService(db)


@router.post("", response_model=ApiResponse, status_code=201)
async def criar(
    dados: str = Form(...),
    imagem: UploadFile | None = File(default=None),
    service: CourseService = Depends(get_service),
):
    request = CourseRequest.model_validate_json(dados)
    course = await service.criar(request, imagem)
    return ApiResponse.ok("Curso criado com sucesso", CourseResponse.model_validate(course))


@router.get("", response_model=ApiResponse)
async def listar(
    page: int = Query(default=1, ge=1),
    service: CourseService = Depends(get_service),
):
    key = _key_page(page)
    cached = await cache_get(key)
    if cached is not None:
        return Response(content=cached, media_type="application/json")
    courses = await service.listar(page, PER_PAGE)
    body = serialize(ApiResponse.ok(dados=[CourseResponse.model_validate(c) for c in courses]).model_dump(mode="json"))
    await cache_set(key, body)
    return Response(content=body, media_type="application/json")


@router.get("/{course_id}", response_model=ApiResponse)
async def buscar(course_id: int, service: CourseService = Depends(get_service)):
    key = _key_one(course_id)
    cached = await cache_get(key)
    if cached is not None:
        return Response(content=cached, media_type="application/json")
    course = await service.buscar_por_id(course_id)
    body = serialize(ApiResponse.ok(dados=CourseResponse.model_validate(course)).model_dump(mode="json"))
    await cache_set(key, body)
    return Response(content=body, media_type="application/json")


@router.put("/{course_id}", response_model=ApiResponse)
async def atualizar(course_id: int, request: CourseUpdateRequest, service: CourseService = Depends(get_service)):
    course = await service.atualizar(course_id, request)
    await cache_delete(_key_one(course_id))
    return ApiResponse.ok("Curso atualizado com sucesso", CourseResponse.model_validate(course))


@router.delete("/{course_id}", response_model=ApiResponse)
async def deletar(course_id: int, service: CourseService = Depends(get_service)):
    await service.deletar(course_id)
    await cache_delete(_key_one(course_id))
    return ApiResponse.ok("Curso deletado com sucesso")
