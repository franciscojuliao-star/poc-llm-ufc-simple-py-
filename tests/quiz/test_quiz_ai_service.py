import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.quiz.ai_service import QuizAiService
from app.quiz.schema import QuizGeneratedResponse
from app.quiz.model import Quiz, Question, Alternative
from app.shared.exception import RegraDeNegocioException
from datetime import datetime

QUIZ_JSON_VALIDO = json.dumps({
    "questions": [
        {
            "statement": "O que é Python?",
            "points": 1,
            "order_num": 1,
            "alternatives": [
                {"text": "Uma linguagem", "correct": True},
                {"text": "Um framework", "correct": False},
            ],
        }
    ]
})


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def ai_service(db):
    return QuizAiService(db)


class TestQuizAiService:

    async def test_gerar_quiz_enfileira_task(self, ai_service):
        ai_service._coletar_conteudo_modulo = AsyncMock(return_value="Conteúdo das aulas")

        with patch("app.quiz.ai_service.gerar_quiz_task") as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-quiz-abc")
            result = await ai_service.gerar_quiz(module_id=1, quantidade=5)

        mock_task.delay.assert_called_once_with(1, "Conteúdo das aulas", 5)
        assert result["task_id"] == "task-quiz-abc"
        assert result["status"] == "PROCESSING"

    async def test_gerar_quiz_lanca_excecao_sem_conteudo(self, ai_service):
        ai_service._coletar_conteudo_modulo = AsyncMock(return_value="")

        with pytest.raises(RegraDeNegocioException):
            await ai_service.gerar_quiz(module_id=1)

    async def test_buscar_pendente_retorna_quiz_deserializado(self, ai_service):
        with patch("app.quiz.ai_service.get_async_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = QUIZ_JSON_VALIDO
            mock_get_redis.return_value = mock_redis

            result = await ai_service.buscar_pendente(1)

        assert isinstance(result, QuizGeneratedResponse)
        assert len(result.questions) == 1

    async def test_buscar_pendente_lanca_excecao_sem_pendente(self, ai_service):
        with patch("app.quiz.ai_service.get_async_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            with pytest.raises(RegraDeNegocioException):
                await ai_service.buscar_pendente(99)

    async def test_confirmar_quiz_salva_e_deleta_redis(self, ai_service):
        quiz_salvo = Quiz(id=1, module_id=1, questions=[],
                          created_at=datetime.now(), updated_at=datetime.now())
        ai_service.quiz_service.criar = AsyncMock(return_value=quiz_salvo)

        with patch("app.quiz.ai_service.get_async_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = QUIZ_JSON_VALIDO
            mock_get_redis.return_value = mock_redis

            result = await ai_service.confirmar_quiz(module_id=1)

        assert result.module_id == 1
        mock_redis.delete.assert_called_once_with("pending:quiz:1")

    async def test_coletar_conteudo_concatena_aulas(self, ai_service):
        from app.lesson.model import Lesson
        lessons = [
            Lesson(id=1, content_editor="Conteúdo A", file_path=None, file_type=None),
            Lesson(id=2, content_editor="Conteúdo B", file_path=None, file_type=None),
        ]
        ai_service._lesson_repo.find_by_module = AsyncMock(return_value=lessons)

        result = await ai_service._coletar_conteudo_modulo(1)

        assert "Conteúdo A" in result
        assert "Conteúdo B" in result

    async def test_coletar_conteudo_ignora_aulas_sem_editor(self, ai_service):
        from app.lesson.model import Lesson
        lessons = [
            Lesson(id=1, content_editor="Conteúdo A", file_path=None),
            Lesson(id=2, content_editor=None, file_path="aula.pdf"),
        ]
        ai_service._lesson_repo.find_by_module = AsyncMock(return_value=lessons)

        result = await ai_service._coletar_conteudo_modulo(1)

        assert "Conteúdo A" in result
        assert result.count("\n\n") == 0

    def test_parse_quiz_valido(self, ai_service):
        result = ai_service._parse_quiz(QUIZ_JSON_VALIDO)

        assert isinstance(result, QuizGeneratedResponse)
        assert len(result.questions) == 1

    def test_parse_quiz_invalido_lanca_excecao(self, ai_service):
        with pytest.raises(RegraDeNegocioException):
            ai_service._parse_quiz("não é json")
