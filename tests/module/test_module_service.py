import pytest
from unittest.mock import MagicMock, patch
from app.module.service import ModuleService
from app.module.schema import ModuleRequest
from app.module.model import Module
from app.shared.exception import RecursoNaoEncontradoException


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return ModuleService(db)


class TestModuleService:

    def test_criar_modulo_sem_imagem(self, service):
        service.repository.count_by_course = MagicMock(return_value=0)
        service.repository.save = MagicMock(side_effect=lambda m: m)
        service.course_repository.find_by_id = MagicMock(return_value=MagicMock(id=1))

        request = ModuleRequest(name="Módulo 1")
        result = service.criar(course_id=1, request=request, imagem=None)

        assert result.name == "Módulo 1"
        assert result.order_num == 1
        assert result.course_id == 1
        assert result.image_path is None

    def test_criar_modulo_order_num_incrementa(self, service):
        service.repository.count_by_course = MagicMock(return_value=2)
        service.repository.save = MagicMock(side_effect=lambda m: m)
        service.course_repository.find_by_id = MagicMock(return_value=MagicMock(id=1))

        request = ModuleRequest(name="Módulo 3")
        result = service.criar(course_id=1, request=request, imagem=None)

        assert result.order_num == 3

    def test_criar_modulo_lanca_excecao_se_curso_nao_existe(self, service):
        service.course_repository.find_by_id = MagicMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            service.criar(course_id=99, request=ModuleRequest(name="M"), imagem=None)

    def test_listar_por_curso(self, service):
        modules = [Module(id=1, name="M1", order_num=1, course_id=1),
                   Module(id=2, name="M2", order_num=2, course_id=1)]
        service.repository.find_by_course = MagicMock(return_value=modules)

        result = service.listar_por_curso(1)

        assert len(result) == 2

    def test_buscar_por_id_retorna_modulo(self, service):
        module = Module(id=1, name="M1", order_num=1, course_id=1)
        service.repository.find_by_id = MagicMock(return_value=module)

        result = service.buscar_por_id(1)

        assert result.id == 1

    def test_buscar_por_id_lanca_excecao_quando_nao_encontrado(self, service):
        service.repository.find_by_id = MagicMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            service.buscar_por_id(99)
