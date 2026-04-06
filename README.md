# PoC LLM UFC Simples — Python

Prova de conceito de uma plataforma LMS (Learning Management System) com IA embarcada.
O foco é o fluxo de criação de conteúdo assistida por inteligência artificial — sem autenticação, sem segurança.

Desenvolvido por **Aglayrton Julião** com **Desenvolvimento Assistido por IA**.

> Versão Java: [poc-llm-ufc-simples](https://github.com/franciscojuliao-star/poc-llm-ufc-simples)

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Framework | FastAPI |
| Banco de Dados | PostgreSQL 16 |
| Migrations | Alembic |
| ORM | SQLAlchemy 2.0 (async) |
| IA | Groq via OpenAI SDK (llama-3.3-70b-versatile) |
| Leitura de PDF | pdfplumber |
| Validação | Pydantic v2 |
| Processamento Assíncrono | Celery + Redis |
| Testes | pytest |
| Servidor | Uvicorn |

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

## Estrutura de Pacotes

```
app/
├── main.py
├── core/         → config (settings via pydantic-settings)
├── db/           → base declarativa + session SQLAlchemy async
├── course/       → model · schema · repository · service · router
├── module/       → model · schema · repository · service · router
├── lesson/       → model · schema · repository · service · ai_service · router
├── quiz/         → model · schema · repository · service · ai_service · router
├── shared/       → ApiResponse · exceções · dependências · redis_client
└── worker/       → celery_app · lesson_tasks · quiz_tasks
alembic/          → migrations automáticas
tests/            → testes unitários por domínio (TDD)
```

---

## Pré-requisitos

- Python 3.12+
- PostgreSQL 16
- Redis
- Conta no [Groq](https://console.groq.com) com uma API Key (`gsk_...`)

---

## Como Rodar

### 1. Criar o banco de dados e o usuário

```sql
CREATE USER poc_user WITH PASSWORD 'poc123';
CREATE DATABASE poc_llm_simple_py OWNER poc_user;
```

### 2. Criar o ambiente virtual e instalar dependências

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz (não versionado):

```bash
DB_URL=postgresql://poc_user:poc123@localhost:5432/poc_llm_simple_py
ASYNC_DB_URL=postgresql+asyncpg://poc_user:poc123@localhost:5432/poc_llm_simple_py
GROQ_API_KEY=gsk_sua_chave_aqui
UPLOAD_DIR=uploads
REDIS_URL=redis://localhost:6379/0
```

### 4. Executar as migrations

```bash
alembic upgrade head
```

### 5. Rodar a aplicação

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Rodar o Celery worker (em outro terminal)

```bash
celery -A app.worker.celery_app worker --loglevel=info
```

### 7. Swagger UI

Documentação interativa disponível em:

```
http://localhost:8000/docs
```

Documentação alternativa (ReDoc):

```
http://localhost:8000/redoc
```

---

## Testando com Postman

O arquivo `poc-llm-ufc-simple-py.postman_collection.json` na raiz do projeto contém todos os endpoints organizados por domínio.

**Como importar:**
1. Abra o Postman
2. Clique em **Import**
3. Selecione o arquivo `poc-llm-ufc-simple-py.postman_collection.json`

**Pastas disponíveis na collection:**

| Pasta | Descrição |
|---|---|
| Cursos | CRUD completo de cursos, com suporte a imagem de capa |
| Módulos | CRUD completo de módulos vinculados a um curso |
| Aulas | CRUD completo de aulas com suporte a texto e upload de PDF |
| IA — Conteúdo da Aula | Geração, revisão e confirmação de conteúdo via IA |
| Quiz — Manual | Criação manual de quiz, perguntas e alternativas |
| Quiz — IA | Geração, revisão e confirmação de quiz via IA |

---

## Fluxo Completo da Aplicação

### 1. Criar o Curso

```
POST /courses
Content-Type: multipart/form-data

dados: { "title": "...", "category": "...", "description": "..." }
imagem: (opcional)
```

Atualizar ou deletar:

```
PUT    /courses/{id}   → atualiza título, categoria ou descrição
DELETE /courses/{id}   → remove o curso
```

### 2. Criar o Módulo

```
POST /courses/{course_id}/modules
Content-Type: multipart/form-data

dados: { "name": "..." }
imagem: (opcional)
```

Atualizar ou deletar:

```
PUT    /modules/{id}   → atualiza nome
DELETE /modules/{id}   → remove o módulo
```

### 3. Criar as Aulas

Aula com conteúdo em texto:

```
POST /modules/{module_id}/lessons
Content-Type: multipart/form-data

dados: { "name": "...", "content_editor": "Texto da aula..." }
```

Aula com PDF (a IA extrai o texto automaticamente):

```
POST /modules/{module_id}/lessons
Content-Type: multipart/form-data

dados: { "name": "..." }
arquivo: arquivo.pdf
```

Atualizar ou deletar:

```
PUT    /lessons/{id}   → atualiza nome ou conteúdo do editor
DELETE /lessons/{id}   → remove a aula
```

### 4. Gerar Conteúdo com IA

A IA usa o `content_editor` ou o texto extraído do PDF como base para gerar conteúdo HTML estruturado.
A geração é processada de forma assíncrona via Celery + Redis.

```
POST /lessons/{id}/gerar-conteudo      → enfileira task e retorna task_id
GET  /lessons/{id}/conteudo-pendente   → visualiza o conteúdo gerado (aguarda processamento)
POST /lessons/{id}/confirmar-conteudo  → salva no banco
POST /lessons/{id}/regerar-conteudo    → regera se não gostar
```

### 5. Gerar Quiz com IA

A IA usa o conteúdo das aulas do módulo para gerar perguntas de múltipla escolha.
A geração é processada de forma assíncrona via Celery + Redis.

```
POST /modules/{id}/quiz/gerar?quantidade=5   → enfileira task e retorna task_id
GET  /modules/{id}/quiz/pendente              → visualiza o quiz gerado (aguarda processamento)
POST /modules/{id}/quiz/confirmar             → salva no banco
POST /modules/{id}/quiz/regerar?quantidade=5  → regera se não gostar
```

### 6. Quiz Manual (opcional)

Criar quiz com perguntas e alternativas em uma única requisição:

```
POST /modules/{id}/quiz
Content-Type: application/json

{
  "questions": [
    {
      "statement": "Pergunta?",
      "points": 1,
      "alternatives": [
        { "text": "Correta", "correct": true },
        { "text": "Errada", "correct": false }
      ]
    }
  ]
}
```

Adicionar perguntas e alternativas individualmente:

```
POST /quiz/{quiz_id}/questions
POST /questions/{question_id}/alternatives
```

Configurar exibição do quiz:

```
POST /quiz/{quiz_id}
{ "show_wrong_answers": true, "show_correct_answers": true, "show_points": true }
```

---

## Resposta Padrão da API

Todas as respostas seguem o padrão:

```json
{
  "sucesso": true,
  "mensagem": "Mensagem descritiva",
  "dados": {},
  "timestamp": "2026-04-01T10:00:00"
}
```

---

## Rodando os Testes

```bash
GROQ_API_KEY=placeholder pytest
```

61 testes unitários cobrindo todos os serviços: `CourseService`, `ModuleService`, `LessonService`, `LessonAiService`, `QuizService` e `QuizAiService`.

---

## Comparação com a versão Java

| Aspecto | Java | Python |
|---|---|---|
| Framework | Spring Boot 3.4 | FastAPI |
| ORM | JPA + Hibernate | SQLAlchemy 2.0 |
| Migrations | Flyway | Alembic |
| IA | Spring AI | OpenAI SDK |
| Leitura PDF | Apache PDFBox | pdfplumber |
| Validação | Bean Validation | Pydantic v2 |
| Processamento Assíncrono | Spring @Async / Virtual Threads | Celery + Redis |
| Testes | JUnit 5 + Mockito | pytest + unittest.mock |
| Porta padrão | 8080 | 8000 |
| Docs | SpringDoc Swagger | FastAPI Swagger (nativo) |
