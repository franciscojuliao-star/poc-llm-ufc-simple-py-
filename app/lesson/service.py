import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.lesson.model import Lesson
from app.lesson.repository import LessonRepository
from app.lesson.schema import LessonRequest
from app.module.repository import ModuleRepository
from app.shared.exception import RecursoNaoEncontradoException, RegraDeNegocioException
from app.core.config import settings


class LessonService:
    def __init__(self, db: AsyncSession):
        self.repository = LessonRepository(db)
        self.module_repository = ModuleRepository(db)

    async def criar(self, module_id: int, request: LessonRequest, arquivo: UploadFile | None) -> Lesson:
        if not await self.module_repository.find_by_id(module_id):
            raise RecursoNaoEncontradoException(f"Módulo {module_id} não encontrado")
        if arquivo and arquivo.content_type != "application/pdf":
            raise RegraDeNegocioException("Apenas arquivos PDF são aceitos")
        order_num = await self.repository.count_by_module(module_id) + 1
        file_path, file_type = None, None
        if arquivo:
            file_path = self._salvar_arquivo(arquivo)
            file_type = "PDF"
        lesson = Lesson(
            name=request.name,
            order_num=order_num,
            module_id=module_id,
            content_editor=request.content_editor,
            file_path=file_path,
            file_type=file_type,
        )
        return await self.repository.save(lesson)

    async def listar_por_modulo(self, module_id: int) -> list[Lesson]:
        return await self.repository.find_by_module(module_id)

    async def buscar_por_id(self, lesson_id: int) -> Lesson:
        return await self.buscar_entidade(lesson_id)

    async def buscar_entidade(self, lesson_id: int) -> Lesson:
        lesson = await self.repository.find_by_id(lesson_id)
        if not lesson:
            raise RecursoNaoEncontradoException(f"Aula {lesson_id} não encontrada")
        return lesson

    async def salvar_conteudo_gerado(self, lesson: Lesson) -> Lesson:
        return await self.repository.save(lesson)

    def _salvar_arquivo(self, arquivo: UploadFile) -> str:
        conteudo = arquivo.file.read()
        ext = os.path.splitext(arquivo.filename)[-1] or ".pdf"
        filename = f"{uuid.uuid4()}{ext}"
        upload_dir = os.path.join(settings.UPLOAD_DIR, "lessons")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(conteudo)
        return filepath
