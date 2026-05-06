# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## O que é

PoC simplificada de uma plataforma LMS com IA embarcada.
Sem segurança, sem autenticação — foco total no fluxo de criação de conteúdo com IA.
Professor único seedado via Alembic. Sem login, sem token.

## Stack

Python 3.12 · FastAPI · PostgreSQL 16 · Alembic · SQLAlchemy
Groq via openai SDK (llama-3.3-70b-versatile) · pdfplumber
Pydantic v2 · pytest · Uvicorn · Celery + Redis (background tasks)

---

## Desenvolvimento Rápido

### Setup Inicial

```bash
# 1. Criar banco de dados PostgreSQL
psql -U postgres
CREATE USER poc_user WITH PASSWORD 'poc123';
CREATE DATABASE poc_llm_simple_py OWNER poc_user;
\q

# 2. Instalar dependências
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Configurar variáveis de ambiente (.env)
DB_URL=postgresql://poc_user:poc123@localhost:5432/poc_llm_simple_py
ASYNC_DB_URL=postgresql+asyncpg://poc_user:poc123@localhost:5432/poc_llm_simple_py
GROQ_API_KEY=gsk_sua_chave_aqui
UPLOAD_DIR=uploads
REDIS_URL=redis://localhost:6379/0

# 4. Rodar migrations
alembic upgrade head
```

### Comandos Essenciais

```bash
# Testes
GROQ_API_KEY=placeholder pytest                    # Todos
GROQ_API_KEY=placeholder pytest tests/course/      # Apenas um módulo
GROQ_API_KEY=placeholder pytest -v tests/          # Verbose
GROQ_API_KEY=placeholder pytest -k test_name       # Testes específicos

# Servidor dev (em um terminal)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Celery worker para background tasks (em outro terminal)
celery -A app.worker.celery_app worker --loglevel=info

# Migrations
alembic upgrade head                # Aplicar migrations
alembic downgrade -1                # Desfazer última migration
alembic revision -m "Descrição"     # Criar nova migration

# Swagger UI
http://localhost:8000/docs          # Documentação interativa
```

---

## Modelo de Dados

```
Course    (1) ──> (N) Module
Module    (1) ──> (N) Lesson
Module    (1) ──> (0..1) Quiz
Quiz      (1) ──> (N) Question
Question  (1) ──> (N) Alternative
```

---

## Estrutura de Módulos

```
app/
  main.py                      → Aplicação FastAPI, routers, exception handlers
  core/
    config.py                  → Settings via pydantic-settings (carrega .env)
  db/
    base.py                    → Base declarativa SQLAlchemy
    session.py                 → AsyncSession factory
  course/                       → router · service · repository · model · schema
  module/                       → router · service · repository · model · schema
  lesson/                       → router · service · repository · model · schema · ai_service
  quiz/                         → router · service · repository · model · schema · ai_service
  shared/
    exception.py                → Custom exceptions + handlers
    schema.py                   → ApiResponse padrão
    redis_client.py             → Client Redis assíncrono
  worker/
    celery_app.py               → Configuração Celery
    lesson_tasks.py             → Background tasks para Lesson
    quiz_tasks.py               → Background tasks para Quiz

tests/
  conftest.py                  → Fixtures pytest (db fixture com SQLite em memória)
  course/, module/, lesson/, quiz/  → Testes por domínio (TDD)
```

---

## Convenções de Código

- **Idioma**: inglês para entidades, campos, métodos e variáveis
- **Módulo raiz**: `app`
- **Schemas separados**: `XxxRequest` (entrada) e `XxxResponse` (saída)
- **Timestamps**: todos os models possuem `created_at` e `updated_at`
- **API response padrão**:
  ```json
  { "sucesso": true, "mensagem": "", "dados": {}, "timestamp": "" }
  ```
- **Commits**: português imperativo (e.g., "Adiciona endpoint de criação de curso")

---

## Padrões de Código

### Estrutura de Domínio (Domain-Driven Design)

Cada domínio (`course`, `module`, `lesson`, `quiz`) segue:

- **model.py**: SQLAlchemy ORM model com `__tablename__`, coluna `id`, `created_at`, `updated_at`
- **schema.py**: Pydantic schemas (`XxxRequest`, `XxxResponse`) com validações
- **repository.py**: Camada de acesso a dados (queries, CRUD)
- **service.py**: Lógica de negócio (validações, orquestração)
- **router.py**: FastAPI endpoints (depende de session da request)
- **exception.py** (opcional): Exceções customizadas do domínio

### Padrão de Database Session

```python
# Em router.py
from app.db.session import get_session

async def endpoint(
    service: Annotated[CourseService, Depends(get_service)],
    session: AsyncSession = Depends(get_session)
):
    return await service.method(session)

# Em service.py
async def method(self, session: AsyncSession):
    repo = CourseRepository(session)
    result = await repo.find_by_id(id)
    return result
```

### Processamento Assíncrono

- **Geração de conteúdo**: enfileirado em Celery → salvo em Redis → consultado via GET
- Tasks: `app/worker/lesson_tasks.py` e `app/worker/quiz_tasks.py`
- Endpoints: `POST /lessons/{id}/gerar-conteudo` → retorna `task_id`; `GET /lessons/{id}/conteudo-pendente` → recupera resultado

---

## Testing (TDD)

### Estrutura de Testes

```python
# tests/conftest.py
@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncSession:
    # SQLite em memória para testes rápidos, sem dependência de PostgreSQL
```

Testes usando a fixture:

```python
@pytest.mark.asyncio
async def test_method(db: AsyncSession):
    repo = CourseRepository(db)
    result = await repo.create(...)
    assert result.id is not None
```

### Padrão TDD

1. **Escreve o teste** (deve falhar)
2. **Roda pytest** e confirma falha
3. **Implementa mínimo** para passar
4. **Roda pytest** novamente
5. Refatora se necessário

**Importante**: Testes precisam da fixture `db` assíncrona. Não mockar repositórios — usar SQLite real.

---

## Método de Trabalho

### TDD — Test Driven Development

- Testes escritos ANTES da implementação
- Ordem: escreve o teste → roda (falha) → implementa → roda (passa)
- Quando a IA errar: descreva o erro, não corrija manualmente

### Método Akita

- Nunca pule etapas — implemente na ordem definida
- Uma responsabilidade por módulo/classe
- Não antecipe funcionalidades futuras
- Código simples e direto; complexidade só quando necessária
- Ao encontrar um problema: pare, entenda a causa raiz, resolva na origem

---

## Comandos Customizados

```
/arquitetura            → Entidades, tabelas SQL, endpoints REST
/regras-negocio         → Regras de negócio do sistema
/requisitos-funcionais  → Requisitos funcionais da PoC
```
