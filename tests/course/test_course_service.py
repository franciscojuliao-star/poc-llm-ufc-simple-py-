import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.course.service import CourseService
from app.course.schema import CourseRequest
from app.course.model import Course
from app.shared.exception import RecursoNaoEncontradoException


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return CourseService(db)


class TestCourseService:

    async def test_criar_curso_sem_imagem(self, service):
        request = CourseRequest(title="Python Web", category="Programação", description="Curso de Python")
        service.repository.save = AsyncMock(side_effect=lambda c: c)

        result = await service.criar(request, imagem=None)

        assert result.title == "Python Web"
        assert result.category == "Programação"
        assert result.image_path is None
        service.repository.save.assert_called_once()

    async def test_criar_curso_salva_imagem(self, service, tmp_path):
        request = CourseRequest(title="Ruby", category="Programação", description="Curso de Ruby")
        service.repository.save = AsyncMock(side_effect=lambda c: c)

        imagem = MagicMock()
        imagem.filename = "capa.jpg"
        imagem.content_type = "image/jpeg"
        imagem.file.read.return_value = b"\xff\xd8\xff" + b"\x00" * 10

        with patch("app.course.service.settings") as mock_settings:
            mock_settings.UPLOAD_DIR = str(tmp_path)
            result = await service.criar(request, imagem=imagem)

        assert result.image_path is not None
        service.repository.save.assert_called_once()

    async def test_criar_curso_rejeita_arquivo_nao_imagem(self, service):
        request = CourseRequest(title="Ruby", category="Programação", description="Curso de Ruby")

        imagem = MagicMock()
        imagem.filename = "arquivo.pdf"
        imagem.content_type = "application/pdf"
        imagem.file.read.return_value = b"%PDF"

        with pytest.raises(Exception):
            await service.criar(request, imagem=imagem)

    async def test_listar_retorna_todos_os_cursos(self, service):
        courses = [
            Course(id=1, title="Python", category="Prog", description="Desc"),
            Course(id=2, title="Ruby", category="Prog", description="Desc"),
        ]
        service.repository.find_all = AsyncMock(return_value=courses)

        result = await service.listar()

        assert len(result) == 2
        service.repository.find_all.assert_called_once()

    async def test_buscar_por_id_retorna_curso(self, service):
        course = Course(id=1, title="Python", category="Prog", description="Desc")
        service.repository.find_by_id = AsyncMock(return_value=course)

        result = await service.buscar_por_id(1)

        assert result.id == 1
        assert result.title == "Python"

    async def test_buscar_por_id_lanca_excecao_quando_nao_encontrado(self, service):
        service.repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.buscar_por_id(99)

    async def test_atualizar_curso_altera_campos(self, service):
        from app.course.schema import CourseUpdateRequest
        course = Course(id=1, title="Python", category="Prog", description="Desc")
        service.repository.find_by_id = AsyncMock(return_value=course)
        service.repository.save = AsyncMock(side_effect=lambda c: c)

        request = CourseUpdateRequest(title="Python Avançado", description="Nova desc")
        result = await service.atualizar(1, request)

        assert result.title == "Python Avançado"
        assert result.description == "Nova desc"
        assert result.category == "Prog"

    async def test_atualizar_curso_lanca_excecao_quando_nao_encontrado(self, service):
        from app.course.schema import CourseUpdateRequest
        service.repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.atualizar(99, CourseUpdateRequest())

    async def test_deletar_curso_chama_delete(self, service):
        course = Course(id=1, title="Python", category="Prog", description="Desc")
        service.repository.find_by_id = AsyncMock(return_value=course)
        service.repository.delete = AsyncMock()

        await service.deletar(1)

        service.repository.delete.assert_called_once_with(course)

    async def test_deletar_curso_lanca_excecao_quando_nao_encontrado(self, service):
        service.repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.deletar(99)
