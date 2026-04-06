import pytest
from unittest.mock import MagicMock, AsyncMock, patch
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

    async def test_criar_modulo_sem_imagem(self, service):
        service.repository.count_by_course = AsyncMock(return_value=0)
        service.repository.save = AsyncMock(side_effect=lambda m: m)
        service.course_repository.find_by_id = AsyncMock(return_value=MagicMock(id=1))

        request = ModuleRequest(name="Módulo 1")
        result = await service.criar(course_id=1, request=request, imagem=None)

        assert result.name == "Módulo 1"
        assert result.order_num == 1
        assert result.course_id == 1
        assert result.image_path is None

    async def test_criar_modulo_order_num_incrementa(self, service):
        service.repository.count_by_course = AsyncMock(return_value=2)
        service.repository.save = AsyncMock(side_effect=lambda m: m)
        service.course_repository.find_by_id = AsyncMock(return_value=MagicMock(id=1))

        request = ModuleRequest(name="Módulo 3")
        result = await service.criar(course_id=1, request=request, imagem=None)

        assert result.order_num == 3

    async def test_criar_modulo_lanca_excecao_se_curso_nao_existe(self, service):
        service.course_repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.criar(course_id=99, request=ModuleRequest(name="M"), imagem=None)

    async def test_listar_por_curso(self, service):
        modules = [
            Module(id=1, name="M1", order_num=1, course_id=1),
            Module(id=2, name="M2", order_num=2, course_id=1),
        ]
        service.repository.find_by_course = AsyncMock(return_value=modules)

        result = await service.listar_por_curso(1)

        assert len(result) == 2

    async def test_buscar_por_id_retorna_modulo(self, service):
        module = Module(id=1, name="M1", order_num=1, course_id=1)
        service.repository.find_by_id = AsyncMock(return_value=module)

        result = await service.buscar_por_id(1)

        assert result.id == 1

    async def test_buscar_por_id_lanca_excecao_quando_nao_encontrado(self, service):
        service.repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.buscar_por_id(99)

    async def test_atualizar_modulo_altera_nome(self, service):
        from app.module.schema import ModuleUpdateRequest
        module = Module(id=1, name="Módulo 1", order_num=1, course_id=1)
        service.repository.find_by_id = AsyncMock(return_value=module)
        service.repository.save = AsyncMock(side_effect=lambda m: m)

        result = await service.atualizar(1, ModuleUpdateRequest(name="Módulo Atualizado"))

        assert result.name == "Módulo Atualizado"

    async def test_atualizar_modulo_lanca_excecao_quando_nao_encontrado(self, service):
        from app.module.schema import ModuleUpdateRequest
        service.repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.atualizar(99, ModuleUpdateRequest())

    async def test_deletar_modulo_chama_delete(self, service):
        module = Module(id=1, name="Módulo 1", order_num=1, course_id=1)
        service.repository.find_by_id = AsyncMock(return_value=module)
        service.repository.delete = AsyncMock()

        await service.deletar(1)

        service.repository.delete.assert_called_once_with(module)

    async def test_deletar_modulo_lanca_excecao_quando_nao_encontrado(self, service):
        service.repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(RecursoNaoEncontradoException):
            await service.deletar(99)
