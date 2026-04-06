import pytest
from unittest.mock import MagicMock, AsyncMock
from app.quiz.service import QuizService
from app.quiz.schema import QuizRequest, QuestionRequest, AlternativeRequest, QuizConfigRequest
from app.quiz.model import Quiz, Question, Alternative
from app.shared.exception import RecursoNaoEncontradoException, RegraDeNegocioException


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return QuizService(db)


def make_question_request(n_alternatives=2, n_correct=1):
    alts = [AlternativeRequest(text=f"Alt {i}", correct=(i == 0 and n_correct > 0)) for i in range(n_alternatives)]
    return QuestionRequest(statement="Pergunta?", alternatives=alts)


class TestQuizService:

    async def test_criar_quiz_com_sucesso(self, service):
        service.module_repository.find_by_id = AsyncMock(return_value=MagicMock(id=1))
        service.quiz_repo.find_by_module = AsyncMock(return_value=None)
        service.quiz_repo.save = AsyncMock(side_effect=lambda q: q)

        request = QuizRequest(questions=[make_question_request()])
        result = await service.criar(module_id=1, request=request)

        assert result.module_id == 1
        assert len(result.questions) == 1

    async def test_criar_quiz_lanca_excecao_se_modulo_nao_existe(self, service):
        service.module_repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.criar(module_id=99, request=QuizRequest(questions=[make_question_request()]))

    async def test_criar_quiz_lanca_excecao_se_ja_existe(self, service):
        service.module_repository.find_by_id = AsyncMock(return_value=MagicMock(id=1))
        service.quiz_repo.find_by_module = AsyncMock(return_value=Quiz(id=1, module_id=1))

        with pytest.raises(RegraDeNegocioException):
            await service.criar(module_id=1, request=QuizRequest(questions=[make_question_request()]))

    async def test_criar_quiz_lanca_excecao_pergunta_sem_alternativas_suficientes(self, service):
        service.module_repository.find_by_id = AsyncMock(return_value=MagicMock(id=1))
        service.quiz_repo.find_by_module = AsyncMock(return_value=None)

        request = QuizRequest(questions=[make_question_request(n_alternatives=1)])
        with pytest.raises(RegraDeNegocioException):
            await service.criar(module_id=1, request=request)

    async def test_criar_quiz_lanca_excecao_sem_alternativa_correta(self, service):
        service.module_repository.find_by_id = AsyncMock(return_value=MagicMock(id=1))
        service.quiz_repo.find_by_module = AsyncMock(return_value=None)

        request = QuizRequest(questions=[make_question_request(n_alternatives=2, n_correct=0)])
        with pytest.raises(RegraDeNegocioException):
            await service.criar(module_id=1, request=request)

    async def test_buscar_por_modulo_retorna_quiz(self, service):
        quiz = Quiz(id=1, module_id=1)
        service.quiz_repo.find_by_module = AsyncMock(return_value=quiz)

        result = await service.buscar_por_modulo(1)

        assert result.id == 1

    async def test_buscar_por_modulo_lanca_excecao_se_nao_existe(self, service):
        service.quiz_repo.find_by_module = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.buscar_por_modulo(1)

    async def test_configurar_quiz(self, service):
        quiz = Quiz(id=1, module_id=1, show_points=False)
        service.quiz_repo.find_by_id = AsyncMock(return_value=quiz)
        service.quiz_repo.save = AsyncMock(side_effect=lambda q: q)

        result = await service.configurar(quiz_id=1, request=QuizConfigRequest(show_points=True))

        assert result.show_points is True

    async def test_adicionar_pergunta_valida(self, service):
        quiz = Quiz(id=1, module_id=1)
        service.quiz_repo.find_by_id = AsyncMock(return_value=quiz)
        service.question_repo.count_by_quiz = AsyncMock(return_value=0)
        service.question_repo.save = AsyncMock(side_effect=lambda q: q)
        service.alternative_repo.save = AsyncMock(side_effect=lambda a: a)

        request = make_question_request()
        result = await service.adicionar_pergunta(quiz_id=1, request=request)

        assert result.statement == "Pergunta?"
        assert result.order_num == 1

    async def test_adicionar_pergunta_lanca_excecao_menos_de_2_alternativas(self, service):
        quiz = Quiz(id=1, module_id=1)
        service.quiz_repo.find_by_id = AsyncMock(return_value=quiz)

        with pytest.raises(RegraDeNegocioException):
            await service.adicionar_pergunta(quiz_id=1, request=make_question_request(n_alternatives=1))

    async def test_adicionar_alternativa_valida(self, service):
        question = Question(id=1, statement="Q?", order_num=1, quiz_id=1)
        service.question_repo.find_by_id = AsyncMock(return_value=question)
        service.alternative_repo.save = AsyncMock(side_effect=lambda a: a)

        request = AlternativeRequest(text="Opção A", correct=True)
        result = await service.adicionar_alternativa(question_id=1, request=request)

        assert result.text == "Opção A"
        assert result.correct is True

    async def test_listar_perguntas(self, service):
        questions = [Question(id=1, statement="Q1", order_num=1, quiz_id=1)]
        service.quiz_repo.find_by_id = AsyncMock(return_value=Quiz(id=1, module_id=1))
        service.question_repo.find_by_quiz = AsyncMock(return_value=questions)

        result = await service.listar_perguntas(1)

        assert len(result) == 1

    async def test_listar_alternativas(self, service):
        alts = [Alternative(id=1, text="A", correct=True, question_id=1)]
        service.question_repo.find_by_id = AsyncMock(
            return_value=Question(id=1, statement="Q?", order_num=1, quiz_id=1)
        )
        service.alternative_repo.find_by_question = AsyncMock(return_value=alts)

        result = await service.listar_alternativas(1)

        assert len(result) == 1
