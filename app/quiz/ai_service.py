import json
import re
from openai import OpenAI
from sqlalchemy.orm import Session
from app.quiz.model import Quiz
from app.quiz.schema import QuizGeneratedResponse, QuizRequest, QuestionRequest, AlternativeRequest
from app.quiz.service import QuizService
from app.lesson.repository import LessonRepository
from app.shared.exception import RegraDeNegocioException
from app.core.config import settings

_pending_quiz: dict[int, QuizGeneratedResponse] = {}


class QuizAiService:
    def __init__(self, db: Session):
        self.quiz_service = QuizService(db)
        self._lesson_repo = LessonRepository(db)
        self._pending = _pending_quiz

    def gerar_quiz(self, module_id: int, quantidade: int = 5) -> QuizGeneratedResponse:
        conteudo = self._coletar_conteudo_modulo(module_id)
        if not conteudo or not conteudo.strip():
            raise RegraDeNegocioException("Não há conteúdo legível nas aulas deste módulo para gerar o quiz")

        client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Você é um especialista em educação. Com base no conteúdo abaixo, gere {quantidade} "
                        "perguntas de múltipla escolha com 4 alternativas cada. Exatamente 1 alternativa deve ser correta. "
                        "Retorne APENAS um JSON válido no formato:\n"
                        '{"questions": [{"statement": "...", "points": 1, "order_num": 1, '
                        '"alternatives": [{"text": "...", "correct": true/false}]}]}\n\n'
                        f"Conteúdo:\n{conteudo}"
                    ),
                }
            ],
        )
        raw = response.choices[0].message.content
        result = self._parse_quiz(raw)
        self._pending[module_id] = result
        return result

    def buscar_pendente(self, module_id: int) -> QuizGeneratedResponse:
        pendente = self._pending.get(module_id)
        if not pendente:
            raise RegraDeNegocioException("Nenhum quiz pendente para este módulo")
        return pendente

    def confirmar_quiz(self, module_id: int) -> Quiz:
        pendente = self.buscar_pendente(module_id)
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
        quiz = self.quiz_service.criar(module_id, request)
        del self._pending[module_id]
        return quiz

    def _coletar_conteudo_modulo(self, module_id: int) -> str:
        lessons = self._lesson_repo.find_by_module(module_id)
        partes = []
        for lesson in lessons:
            if lesson.content_editor:
                partes.append(lesson.content_editor)
        return "\n\n".join(partes)

    def _parse_quiz(self, raw: str) -> QuizGeneratedResponse:
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            texto = match.group(0) if match else raw
            data = json.loads(texto)
            return QuizGeneratedResponse(**data)
        except Exception:
            raise RegraDeNegocioException("Falha ao interpretar o JSON do quiz gerado pela IA")
