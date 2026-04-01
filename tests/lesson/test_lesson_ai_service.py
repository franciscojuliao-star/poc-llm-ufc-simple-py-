import pytest
from unittest.mock import MagicMock, patch
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

    def test_gerar_conteudo_a_partir_de_content_editor(self, ai_service):
        lesson = Lesson(id=1, name="Python", content_editor="Texto base", file_path=None)
        ai_service.lesson_service.buscar_entidade = MagicMock(return_value=lesson)

        with patch("app.lesson.ai_service.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value.choices = [
                MagicMock(message=MagicMock(content="<h2>Python</h2>"))
            ]
            result = ai_service.gerar_conteudo(1)

        assert "<h2>Python</h2>" in result
        assert ai_service._pending[1] == result

    def test_gerar_conteudo_lanca_excecao_sem_fonte(self, ai_service):
        lesson = Lesson(id=1, name="Aula", content_editor=None, file_path=None)
        ai_service.lesson_service.buscar_entidade = MagicMock(return_value=lesson)

        with pytest.raises(RegraDeNegocioException):
            ai_service.gerar_conteudo(1)

    def test_buscar_conteudo_pendente_retorna_conteudo(self, ai_service):
        ai_service._pending[1] = "<h2>Conteúdo</h2>"

        result = ai_service.buscar_conteudo_pendente(1)

        assert result == "<h2>Conteúdo</h2>"

    def test_buscar_conteudo_pendente_lanca_excecao_sem_pendente(self, ai_service):
        with pytest.raises(RegraDeNegocioException):
            ai_service.buscar_conteudo_pendente(99)

    def test_confirmar_conteudo_salva_e_remove_pendente(self, ai_service):
        from datetime import datetime
        lesson = Lesson(id=1, name="Python", content_editor=None, module_id=1,
                        order_num=1, created_at=datetime.now(), updated_at=datetime.now())
        ai_service._pending[1] = "<h2>Python</h2>"
        ai_service.lesson_service.buscar_entidade = MagicMock(return_value=lesson)
        ai_service.lesson_service.salvar_conteudo_gerado = MagicMock(return_value=lesson)

        ai_service.confirmar_conteudo(1)

        assert lesson.content_editor == "<h2>Python</h2>"
        assert 1 not in ai_service._pending
        ai_service.lesson_service.salvar_conteudo_gerado.assert_called_once()

    def test_gerar_conteudo_a_partir_de_pdf(self, ai_service, tmp_path):
        pdf_file = tmp_path / "aula.pdf"
        pdf_file.write_bytes(b"conteudo simulado")

        lesson = Lesson(id=1, name="PDF Aula", content_editor=None, file_path=str(pdf_file), file_type="PDF")
        ai_service.lesson_service.buscar_entidade = MagicMock(return_value=lesson)

        with patch("app.lesson.ai_service.pdfplumber") as mock_pdf, \
             patch("app.lesson.ai_service.OpenAI") as mock_openai:
            mock_pdf.open.return_value.__enter__.return_value.pages = [MagicMock(extract_text=lambda: "Texto do PDF")]
            mock_openai.return_value.chat.completions.create.return_value.choices = [
                MagicMock(message=MagicMock(content="<h2>PDF</h2>"))
            ]
            result = ai_service.gerar_conteudo(1)

        assert "<h2>PDF</h2>" in result

    def test_regerar_sobrescreve_conteudo_pendente(self, ai_service):
        lesson = Lesson(id=1, name="Python", content_editor="Base", file_path=None)
        ai_service._pending[1] = "<h2>Antigo</h2>"
        ai_service.lesson_service.buscar_entidade = MagicMock(return_value=lesson)

        with patch("app.lesson.ai_service.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value.choices = [
                MagicMock(message=MagicMock(content="<h2>Novo</h2>"))
            ]
            result = ai_service.gerar_conteudo(1)

        assert result == "<h2>Novo</h2>"
        assert ai_service._pending[1] == "<h2>Novo</h2>"
