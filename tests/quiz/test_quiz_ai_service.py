import json
import pytest
from unittest.mock import MagicMock, patch
from app.quiz.ai_service import QuizAiService
from app.quiz.schema import QuizGeneratedResponse
from app.quiz.model import Quiz, Question, Alternative
from app.shared.exception import RegraDeNegocioException

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

    def test_gerar_quiz_com_sucesso(self, ai_service):
        ai_service._coletar_conteudo_modulo = MagicMock(return_value="Conteúdo das aulas")

        with patch("app.quiz.ai_service.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value.choices = [
                MagicMock(message=MagicMock(content=QUIZ_JSON_VALIDO))
            ]
            result = ai_service.gerar_quiz(module_id=1, quantidade=1)

        assert isinstance(result, QuizGeneratedResponse)
        assert len(result.questions) == 1
        assert ai_service._pending[1] == result

    def test_gerar_quiz_lanca_excecao_sem_conteudo(self, ai_service):
        ai_service._coletar_conteudo_modulo = MagicMock(return_value="")

        with pytest.raises(RegraDeNegocioException):
            ai_service.gerar_quiz(module_id=1)

    def test_gerar_quiz_lanca_excecao_json_invalido(self, ai_service):
        ai_service._coletar_conteudo_modulo = MagicMock(return_value="Conteúdo")

        with patch("app.quiz.ai_service.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value.choices = [
                MagicMock(message=MagicMock(content="isso não é json"))
            ]
            with pytest.raises(RegraDeNegocioException):
                ai_service.gerar_quiz(module_id=1)

    def test_buscar_pendente_retorna_quiz(self, ai_service):
        quiz = QuizGeneratedResponse(questions=[])
        ai_service._pending[1] = quiz

        result = ai_service.buscar_pendente(1)

        assert result == quiz

    def test_buscar_pendente_lanca_excecao_sem_pendente(self, ai_service):
        with pytest.raises(RegraDeNegocioException):
            ai_service.buscar_pendente(99)

    def test_confirmar_quiz_salva_e_remove_pendente(self, ai_service):
        from datetime import datetime
        quiz_gerado = QuizGeneratedResponse(**json.loads(QUIZ_JSON_VALIDO))
        ai_service._pending[1] = quiz_gerado

        quiz_salvo = Quiz(id=1, module_id=1, questions=[], created_at=datetime.now(), updated_at=datetime.now())
        ai_service.quiz_service.criar = MagicMock(return_value=quiz_salvo)
        ai_service.quiz_service.quiz_repo.find_by_module = MagicMock(return_value=None)

        result = ai_service.confirmar_quiz(module_id=1)

        assert result.module_id == 1
        assert 1 not in ai_service._pending

    def test_regerar_sobrescreve_pendente(self, ai_service):
        quiz_antigo = QuizGeneratedResponse(questions=[])
        ai_service._pending[1] = quiz_antigo
        ai_service._coletar_conteudo_modulo = MagicMock(return_value="Novo conteúdo")

        with patch("app.quiz.ai_service.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value.choices = [
                MagicMock(message=MagicMock(content=QUIZ_JSON_VALIDO))
            ]
            result = ai_service.gerar_quiz(module_id=1)

        assert result != quiz_antigo
        assert ai_service._pending[1] == result

    def test_coletar_conteudo_concatena_aulas(self, ai_service):
        from app.lesson.model import Lesson
        lessons = [
            Lesson(id=1, content_editor="Conteúdo A", file_path=None, file_type=None),
            Lesson(id=2, content_editor="Conteúdo B", file_path=None, file_type=None),
        ]
        ai_service._lesson_repo.find_by_module = MagicMock(return_value=lessons)

        result = ai_service._coletar_conteudo_modulo(1)

        assert "Conteúdo A" in result
        assert "Conteúdo B" in result

    def test_parse_quiz_valido(self, ai_service):
        result = ai_service._parse_quiz(QUIZ_JSON_VALIDO)

        assert isinstance(result, QuizGeneratedResponse)
        assert len(result.questions) == 1

    def test_parse_quiz_invalido_lanca_excecao(self, ai_service):
        with pytest.raises(RegraDeNegocioException):
            ai_service._parse_quiz("não é json")
