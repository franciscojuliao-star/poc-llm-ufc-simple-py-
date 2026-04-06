from fastapi import APIRouter, Depends, UploadFile, File, Form
from app.course.schema import CourseRequest, CourseUpdateRequest, CourseResponse
from app.course.service import CourseService
from app.shared.dependencies import SessionDep
from app.shared.schema import ApiResponse
import json

router = APIRouter(prefix="/courses", tags=["Cursos"])


def get_service(db: SessionDep) -> CourseService:
    return CourseService(db)


@router.post("", response_model=ApiResponse, status_code=201)
async def criar(
    dados: str = Form(...),
    imagem: UploadFile | None = File(default=None),
    service: CourseService = Depends(get_service),
):
    request = CourseRequest(**json.loads(dados))
    course = await service.criar(request, imagem)
    return ApiResponse.ok("Curso criado com sucesso", CourseResponse.model_validate(course))


@router.get("", response_model=ApiResponse)
async def listar(service: CourseService = Depends(get_service)):
    courses = await service.listar()
    return ApiResponse.ok(dados=[CourseResponse.model_validate(c) for c in courses])


@router.get("/{course_id}", response_model=ApiResponse)
async def buscar(course_id: int, service: CourseService = Depends(get_service)):
    course = await service.buscar_por_id(course_id)
    return ApiResponse.ok(dados=CourseResponse.model_validate(course))


@router.put("/{course_id}", response_model=ApiResponse)
async def atualizar(course_id: int, request: CourseUpdateRequest, service: CourseService = Depends(get_service)):
    course = await service.atualizar(course_id, request)
    return ApiResponse.ok("Curso atualizado com sucesso", CourseResponse.model_validate(course))


@router.delete("/{course_id}", response_model=ApiResponse)
async def deletar(course_id: int, service: CourseService = Depends(get_service)):
    await service.deletar(course_id)
    return ApiResponse.ok("Curso deletado com sucesso")
