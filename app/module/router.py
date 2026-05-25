from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import Response
from app.module.schema import ModuleRequest, ModuleUpdateRequest, ModuleResponse
from app.module.service import ModuleService
from app.shared.dependencies import SessionDep
from app.shared.schema import ApiResponse
from app.shared.cache import cache_get, cache_set, cache_delete, serialize

router = APIRouter(tags=["Módulos"])


def _key_list(course_id: int) -> str:
    return f"modules:course:{course_id}"


def _key_one(module_id: int) -> str:
    return f"module:{module_id}"


def get_service(db: SessionDep) -> ModuleService:
    return ModuleService(db)


@router.post("/courses/{course_id}/modules", response_model=ApiResponse, status_code=201)
async def criar(
    course_id: int,
    dados: str = Form(...),
    imagem: UploadFile | None = File(default=None),
    service: ModuleService = Depends(get_service),
):
    request = ModuleRequest.model_validate_json(dados)
    module = await service.criar(course_id, request, imagem)
    await cache_delete(_key_list(course_id))
    return ApiResponse.ok("Módulo criado com sucesso", ModuleResponse.model_validate(module))


@router.get("/courses/{course_id}/modules", response_model=ApiResponse)
async def listar(course_id: int, service: ModuleService = Depends(get_service)):
    key = _key_list(course_id)
    cached = await cache_get(key)
    if cached is not None:
        return Response(content=cached, media_type="application/json")
    modules = await service.listar_por_curso(course_id)
    body = serialize(ApiResponse.ok(dados=[ModuleResponse.model_validate(m) for m in modules]).model_dump(mode="json"))
    await cache_set(key, body)
    return Response(content=body, media_type="application/json")


@router.get("/modules/{module_id}", response_model=ApiResponse)
async def buscar(module_id: int, service: ModuleService = Depends(get_service)):
    key = _key_one(module_id)
    cached = await cache_get(key)
    if cached is not None:
        return Response(content=cached, media_type="application/json")
    module = await service.buscar_por_id(module_id)
    body = serialize(ApiResponse.ok(dados=ModuleResponse.model_validate(module)).model_dump(mode="json"))
    await cache_set(key, body)
    return Response(content=body, media_type="application/json")


@router.put("/modules/{module_id}", response_model=ApiResponse)
async def atualizar(module_id: int, request: ModuleUpdateRequest, service: ModuleService = Depends(get_service)):
    module = await service.atualizar(module_id, request)
    await cache_delete(_key_one(module_id))
    return ApiResponse.ok("Módulo atualizado com sucesso", ModuleResponse.model_validate(module))


@router.delete("/modules/{module_id}", response_model=ApiResponse)
async def deletar(module_id: int, service: ModuleService = Depends(get_service)):
    await service.deletar(module_id)
    await cache_delete(_key_one(module_id))
    return ApiResponse.ok("Módulo deletado com sucesso")
