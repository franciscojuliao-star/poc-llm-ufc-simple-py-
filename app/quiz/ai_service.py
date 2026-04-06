import json
import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.quiz.model import Quiz
from app.quiz.schema import QuizGeneratedResponse, QuizRequest, QuestionRequest, AlternativeRequest
from app.quiz.service import QuizService
from app.lesson.repository import LessonRepository
from app.shared.exception import RegraDeNegocioException
from app.shared.redis_client import get_async_redis
from app.worker.quiz_tasks import gerar_quiz_task


class QuizAiService:
    def __init__(self, db: AsyncSession):
        self.quiz_service = QuizService(db)
        self._lesson_repo = LessonRepository(db)

    async def gerar_quiz(self, module_id: int, quantidade: int = 5) -> dict:
        conteudo = await self._coletar_conteudo_modulo(module_id)
        if not conteudo or not conteudo.strip():
            raise RegraDeNegocioException("Não há conteúdo legível nas aulas deste módulo para gerar o quiz")
        task = gerar_quiz_task.delay(module_id, conteudo, quantidade)
        return {"task_id": task.id, "status": "PROCESSING"}

    async def buscar_pendente(self, module_id: int) -> QuizGeneratedResponse:
        redis = await get_async_redis()
        raw = await redis.get(f"pending:quiz:{module_id}")
        if not raw:
            raise RegraDeNegocioException("Nenhum quiz pendente para este módulo")
        return self._parse_quiz(raw)

    async def confirmar_quiz(self, module_id: int) -> Quiz:
        pendente = await self.buscar_pendente(module_id)
        request = QuizRequest(
            questions=[
                QuestionRequest(
                    statement=q.statement,
                    points=q.points,
                    alternatives=[AlternativeRequest(text=a.text, correct=a.correct) for a in q.alternatives],
                )
                for q in pendente.questions
            ]
        )
        quiz = await self.quiz_service.criar(module_id, request)
        redis = await get_async_redis()
        await redis.delete(f"pending:quiz:{module_id}")
        return quiz

    async def _coletar_conteudo_modulo(self, module_id: int) -> str:
        lessons = await self._lesson_repo.find_by_module(module_id)
        partes = [lesson.content_editor for lesson in lessons if lesson.content_editor]
        return "\n\n".join(partes)

    def _parse_quiz(self, raw: str) -> QuizGeneratedResponse:
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            texto = match.group(0) if match else raw
            data = json.loads(texto)
            return QuizGeneratedResponse(**data)
        except Exception:
            raise RegraDeNegocioException("Falha ao interpretar o JSON do quiz gerado pela IA")
