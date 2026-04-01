import pytest
from unittest.mock import MagicMock, patch
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

    def test_criar_curso_sem_imagem(self, service):
        request = CourseRequest(title="Python Web", category="Programação", description="Curso de Python")
        service.repository.save = MagicMock(side_effect=lambda c: c)

        result = service.criar(request, imagem=None)

        assert result.title == "Python Web"
        assert result.category == "Programação"
        assert result.image_path is None
        service.repository.save.assert_called_once()

    def test_criar_curso_salva_imagem(self, service, tmp_path):
        request = CourseRequest(title="Ruby", category="Programação", description="Curso de Ruby")
        service.repository.save = MagicMock(side_effect=lambda c: c)

        imagem = MagicMock()
        imagem.filename = "capa.jpg"
        imagem.content_type = "image/jpeg"
        imagem.file.read.return_value = b"\xff\xd8\xff" + b"\x00" * 10

        with patch("app.course.service.settings") as mock_settings:
            mock_settings.UPLOAD_DIR = str(tmp_path)
            result = service.criar(request, imagem=imagem)

        assert result.image_path is not None
        service.repository.save.assert_called_once()

    def test_criar_curso_rejeita_arquivo_nao_imagem(self, service):
        request = CourseRequest(title="Ruby", category="Programação", description="Curso de Ruby")

        imagem = MagicMock()
        imagem.filename = "arquivo.pdf"
        imagem.content_type = "application/pdf"
        imagem.file.read.return_value = b"%PDF"

        with pytest.raises(Exception):
            service.criar(request, imagem=imagem)

    def test_listar_retorna_todos_os_cursos(self, service):
        courses = [
            Course(id=1, title="Python", category="Prog", description="Desc"),
            Course(id=2, title="Ruby", category="Prog", description="Desc"),
        ]
        service.repository.find_all = MagicMock(return_value=courses)

        result = service.listar()

        assert len(result) == 2
        service.repository.find_all.assert_called_once()

    def test_buscar_por_id_retorna_curso(self, service):
        course = Course(id=1, title="Python", category="Prog", description="Desc")
        service.repository.find_by_id = MagicMock(return_value=course)

        result = service.buscar_por_id(1)

        assert result.id == 1
        assert result.title == "Python"

    def test_buscar_por_id_lanca_excecao_quando_nao_encontrado(self, service):
        service.repository.find_by_id = MagicMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            service.buscar_por_id(99)
