import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.lesson.ai_service import LessonAiService
from app.lesson.model import Lesson
from app.shared.exception import RegraDeNegocioException


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def ai_service(db):
    return LessonAiService(db)


class TestLessonAiService:

    async def test_gerar_conteudo_enfileira_task_e_retorna_task_id(self, ai_service):
        lesson = Lesson(id=1, name="Python", content_editor="Texto base", file_path=None)
        ai_service.lesson_service.buscar_entidade = AsyncMock(return_value=lesson)

        with patch("app.lesson.ai_service.gerar_conteudo_task") as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-abc-123")
            result = await ai_service.gerar_conteudo(1)

        mock_task.delay.assert_called_once_with(1, "Texto base")
        assert result["task_id"] == "task-abc-123"
        assert result["status"] == "PROCESSING"

    async def test_gerar_conteudo_lanca_excecao_sem_fonte(self, ai_service):
        lesson = Lesson(id=1, name="Aula", content_editor=None, file_path=None)
        ai_service.lesson_service.buscar_entidade = AsyncMock(return_value=lesson)

        with pytest.raises(RegraDeNegocioException):
            await ai_service.gerar_conteudo(1)

    async def test_buscar_conteudo_pendente_retorna_conteudo(self, ai_service):
        with patch("app.lesson.ai_service.get_async_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = "<h2>Conteúdo</h2>"
            mock_get_redis.return_value = mock_redis

            result = await ai_service.buscar_conteudo_pendente(1)

        assert result == "<h2>Conteúdo</h2>"

    async def test_buscar_conteudo_pendente_lanca_excecao_sem_pendente(self, ai_service):
        with patch("app.lesson.ai_service.get_async_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            with pytest.raises(RegraDeNegocioException):
                await ai_service.buscar_conteudo_pendente(1)

    async def test_confirmar_conteudo_salva_e_deleta_redis(self, ai_service):
        from datetime import datetime
        lesson = Lesson(id=1, name="Python", content_editor=None, module_id=1,
                        order_num=1, created_at=datetime.now(), updated_at=datetime.now())
        ai_service.lesson_service.buscar_entidade = AsyncMock(return_value=lesson)
        ai_service.lesson_service.salvar_conteudo_gerado = AsyncMock(return_value=lesson)

        with patch("app.lesson.ai_service.get_async_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = "<h2>Python</h2>"
            mock_get_redis.return_value = mock_redis

            await ai_service.confirmar_conteudo(1)

        assert lesson.content_editor == "<h2>Python</h2>"
        mock_redis.delete.assert_called_once_with("pending:lesson:1")
        ai_service.lesson_service.salvar_conteudo_gerado.assert_called_once()

    async def test_gerar_conteudo_a_partir_de_pdf(self, ai_service, tmp_path):
        pdf_file = tmp_path / "aula.pdf"
        pdf_file.write_bytes(b"conteudo simulado")

        lesson = Lesson(id=1, name="PDF Aula", content_editor=None,
                        file_path=str(pdf_file), file_type="PDF")
        ai_service.lesson_service.buscar_entidade = AsyncMock(return_value=lesson)

        with patch("app.lesson.ai_service.pdfplumber") as mock_pdf, \
             patch("app.lesson.ai_service.gerar_conteudo_task") as mock_task:
            mock_pdf.open.return_value.__enter__.return_value.pages = [
                MagicMock(extract_text=lambda: "Texto do PDF")
            ]
            mock_task.delay.return_value = MagicMock(id="task-pdf-456")
            result = await ai_service.gerar_conteudo(1)

        mock_task.delay.assert_called_once_with(1, "Texto do PDF")
        assert result["task_id"] == "task-pdf-456"

    async def test_regerar_enfileira_nova_task(self, ai_service):
        lesson = Lesson(id=1, name="Python", content_editor="Base atualizada", file_path=None)
        ai_service.lesson_service.buscar_entidade = AsyncMock(return_value=lesson)

        with patch("app.lesson.ai_service.gerar_conteudo_task") as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-novo-789")
            result = await ai_service.gerar_conteudo(1)

        assert result["task_id"] == "task-novo-789"
        assert result["status"] == "PROCESSING"
