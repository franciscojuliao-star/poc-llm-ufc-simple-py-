import pdfplumber
from sqlalchemy.ext.asyncio import AsyncSession
from app.lesson.model import Lesson
from app.lesson.schema import LessonResponse
from app.lesson.service import LessonService
from app.shared.exception import RegraDeNegocioException
from app.shared.redis_client import get_async_redis
from app.worker.lesson_tasks import gerar_conteudo_task


class LessonAiService:
    def __init__(self, db: AsyncSession):
        self.lesson_service = LessonService(db)

    async def gerar_conteudo(self, lesson_id: int) -> dict:
        lesson = await self.lesson_service.buscar_entidade(lesson_id)
        fonte = self._extrair_fonte(lesson)
        if not fonte or not fonte.strip():
            raise RegraDeNegocioException("A aula não possui conteúdo legível para gerar via IA")
        task = gerar_conteudo_task.delay(lesson_id, fonte)
        return {"task_id": task.id, "status": "PROCESSING"}

    async def buscar_conteudo_pendente(self, lesson_id: int) -> str:
        redis = await get_async_redis()
        content = await redis.get(f"pending:lesson:{lesson_id}")
        if not content:
            raise RegraDeNegocioException("Nenhum conteúdo pendente para esta aula")
        return content

    async def confirmar_conteudo(self, lesson_id: int) -> LessonResponse:
        conteudo = await self.buscar_conteudo_pendente(lesson_id)
        lesson = await self.lesson_service.buscar_entidade(lesson_id)
        lesson.content_editor = conteudo
        await self.lesson_service.salvar_conteudo_gerado(lesson)
        redis = await get_async_redis()
        await redis.delete(f"pending:lesson:{lesson_id}")
        return LessonResponse.model_validate(lesson)

    def _extrair_fonte(self, lesson: Lesson) -> str | None:
        if lesson.file_path and lesson.file_type == "PDF":
            return self._extrair_texto_pdf(lesson.file_path)
        return lesson.content_editor

    def _extrair_texto_pdf(self, file_path: str) -> str:
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
