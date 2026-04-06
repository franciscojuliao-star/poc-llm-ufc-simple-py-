import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.module.model import Module
from app.module.repository import ModuleRepository
from app.module.schema import ModuleRequest, ModuleUpdateRequest
from app.course.repository import CourseRepository
from app.shared.exception import RecursoNaoEncontradoException, RegraDeNegocioException
from app.core.config import settings


class ModuleService:
    def __init__(self, db: AsyncSession):
        self.repository = ModuleRepository(db)
        self.course_repository = CourseRepository(db)

    async def criar(self, course_id: int, request: ModuleRequest, imagem: UploadFile | None) -> Module:
        if not await self.course_repository.find_by_id(course_id):
            raise RecursoNaoEncontradoException(f"Curso {course_id} não encontrado")
        order_num = await self.repository.count_by_course(course_id) + 1
        image_path = self._salvar_imagem(imagem) if imagem else None
        module = Module(
            name=request.name,
            order_num=order_num,
            course_id=course_id,
            image_path=image_path,
        )
        return await self.repository.save(module)

    async def atualizar(self, module_id: int, request: ModuleUpdateRequest) -> Module:
        module = await self.buscar_por_id(module_id)
        if request.name is not None:
            module.name = request.name
        return await self.repository.save(module)

    async def deletar(self, module_id: int) -> None:
        module = await self.buscar_por_id(module_id)
        await self.repository.delete(module)

    async def listar_por_curso(self, course_id: int) -> list[Module]:
        return await self.repository.find_by_course(course_id)

    async def buscar_por_id(self, module_id: int) -> Module:
        module = await self.repository.find_by_id(module_id)
        if not module:
            raise RecursoNaoEncontradoException(f"Módulo {module_id} não encontrado")
        return module

    def _salvar_imagem(self, imagem: UploadFile) -> str:
        conteudo = imagem.file.read()
        if not imagem.content_type or not imagem.content_type.startswith("image/"):
            raise RegraDeNegocioException("Arquivo enviado não é uma imagem válida")
        ext = os.path.splitext(imagem.filename)[-1] or ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
        upload_dir = os.path.join(settings.UPLOAD_DIR, "modules")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(conteudo)
        return filepath
