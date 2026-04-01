from fastapi import APIRouter, Depends, UploadFile, File, Form
from app.module.schema import ModuleRequest, ModuleResponse
from app.module.service import ModuleService
from app.shared.dependencies import SessionDep
from app.shared.schema import ApiResponse
import json

router = APIRouter(tags=["Módulos"])


def get_service(db: SessionDep) -> ModuleService:
    return ModuleService(db)


@router.post("/courses/{course_id}/modules", response_model=ApiResponse, status_code=201)
async def criar(
    course_id: int,
    dados: str = Form(...),
    imagem: UploadFile | None = File(default=None),
    service: ModuleService = Depends(get_service),
):
    request = ModuleRequest(**json.loads(dados))
    module = await service.criar(course_id, request, imagem)
    return ApiResponse.ok("Módulo criado com sucesso", ModuleResponse.model_validate(module))


@router.get("/courses/{course_id}/modules", response_model=ApiResponse)
async def listar(course_id: int, service: ModuleService = Depends(get_service)):
    modules = await service.listar_por_curso(course_id)
    return ApiResponse.ok(dados=[ModuleResponse.model_validate(m) for m in modules])


@router.get("/modules/{module_id}", response_model=ApiResponse)
async def buscar(module_id: int, service: ModuleService = Depends(get_service)):
    module = await service.buscar_por_id(module_id)
    return ApiResponse.ok(dados=ModuleResponse.model_validate(module))
