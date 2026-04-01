import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.lesson.service import LessonService
from app.lesson.schema import LessonRequest
from app.lesson.model import Lesson
from app.shared.exception import RecursoNaoEncontradoException, RegraDeNegocioException


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return LessonService(db)


class TestLessonService:

    async def test_criar_aula_sem_arquivo(self, service):
        service.repository.count_by_module = AsyncMock(return_value=0)
        service.repository.save = AsyncMock(side_effect=lambda l: l)
        service.module_repository.find_by_id = AsyncMock(return_value=MagicMock(id=1))

        request = LessonRequest(name="Introdução", content_editor="Texto da aula")
        result = await service.criar(module_id=1, request=request, arquivo=None)

        assert result.name == "Introdução"
        assert result.order_num == 1
        assert result.content_editor == "Texto da aula"
        assert result.file_path is None

    async def test_criar_aula_order_num_incrementa(self, service):
        service.repository.count_by_module = AsyncMock(return_value=3)
        service.repository.save = AsyncMock(side_effect=lambda l: l)
        service.module_repository.find_by_id = AsyncMock(return_value=MagicMock(id=1))

        request = LessonRequest(name="Aula 4")
        result = await service.criar(module_id=1, request=request, arquivo=None)

        assert result.order_num == 4

    async def test_criar_aula_lanca_excecao_se_modulo_nao_existe(self, service):
        service.module_repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.criar(module_id=99, request=LessonRequest(name="X"), arquivo=None)

    async def test_criar_aula_rejeita_arquivo_nao_pdf(self, service):
        service.module_repository.find_by_id = AsyncMock(return_value=MagicMock(id=1))
        service.repository.count_by_module = AsyncMock(return_value=0)

        arquivo = MagicMock()
        arquivo.filename = "imagem.jpg"
        arquivo.content_type = "image/jpeg"

        with pytest.raises(RegraDeNegocioException):
            await service.criar(module_id=1, request=LessonRequest(name="X"), arquivo=arquivo)

    async def test_criar_aula_com_pdf(self, service, tmp_path):
        service.repository.count_by_module = AsyncMock(return_value=0)
        service.repository.save = AsyncMock(side_effect=lambda l: l)
        service.module_repository.find_by_id = AsyncMock(return_value=MagicMock(id=1))

        arquivo = MagicMock()
        arquivo.filename = "material.pdf"
        arquivo.content_type = "application/pdf"
        arquivo.file.read.return_value = b"%PDF-1.4 content"

        with patch("app.lesson.service.settings") as mock_settings:
            mock_settings.UPLOAD_DIR = str(tmp_path)
            result = await service.criar(module_id=1, request=LessonRequest(name="Aula PDF"), arquivo=arquivo)

        assert result.file_path is not None
        assert result.file_type == "PDF"

    async def test_listar_por_modulo(self, service):
        lessons = [
            Lesson(id=1, name="L1", order_num=1, module_id=1),
            Lesson(id=2, name="L2", order_num=2, module_id=1),
        ]
        service.repository.find_by_module = AsyncMock(return_value=lessons)

        result = await service.listar_por_modulo(1)

        assert len(result) == 2

    async def test_buscar_por_id_retorna_aula(self, service):
        lesson = Lesson(id=1, name="L1", order_num=1, module_id=1)
        service.repository.find_by_id = AsyncMock(return_value=lesson)

        result = await service.buscar_por_id(1)

        assert result.id == 1

    async def test_buscar_por_id_lanca_excecao_quando_nao_encontrado(self, service):
        service.repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.buscar_por_id(99)
