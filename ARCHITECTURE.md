# ARCHITECTURE.md

Documentação sobre decisões arquiteturais, padrões de design e metodologia de desenvolvimento desta PoC.

---

## Por Que Este Projeto?

Esta PoC explora como integrar LLMs (Large Language Models) em uma plataforma educacional para **automatizar e acelerar a criação de conteúdo**. O objetivo é validar fluxos de:

- Geração de conteúdo estruturado a partir de texto/PDF
- Criação automática de quizzes com base no conteúdo
- Processamento assíncrono para operações longas (IA é lenta)
- Persistência segura em PostgreSQL

**Escopo intencional**: sem autenticação, sem permissões, sem frontend. Apenas o backend REST e a integração com LLM.

---

## Decisões Arquiteturais

### 1. FastAPI + async/await (em vez de Django ou Flask)

**Por quê?**

- **Performance com I/O**: FastAPI é construído sobre Starlette (async-first). Requisições I/O-bound (banco de dados, APIs externas) não bloqueiam outras requisições.
- **Integração natural com IA**: Chamadas à Groq API são síncronas mas lentas (~2s). Async permite que outras requisições sejam processadas enquanto aguardamos a IA.
- **Menos boilerplate**: FastAPI gera Swagger/OpenAPI automaticamente. Validação via Pydantic é expressiva e type-safe.
- **Documentação automática**: `http://localhost:8000/docs` atualiza-se com cada novo endpoint.

```python
# Exemplo: FastAPI com async permite múltiplas requisições simultâneas
@app.get("/lessons/{id}")
async def get_lesson(id: int, session: AsyncSession = Depends(get_session)):
    # Enquanto esta requisição aguarda o banco, outras continuam processadas
    return await LessonRepository(session).find_by_id(id)
```

### 2. PostgreSQL 16 + SQLAlchemy 2.0 async (em vez de SQLite ou ORM síncrono)

**Por quê?**

- **Production-ready**: PostgreSQL é robusto, escalável, suporta transações ACID e índices complexos.
- **SQLAlchemy 2.0 async**: API moderna, type-hints completos, integração natural com FastAPI async.
- **Pool de conexões**: AsyncEngine gerencia um pool de conexões assíncronas, evitando overhead de criar conexão por requisição.

```python
# SQLAlchemy 2.0 async session
engine = create_async_engine(ASYNC_DB_URL)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession)

async def get_session():
    async with SessionLocal() as session:
        yield session
```

### 3. Alembic para Migrations (em vez de Django ORM)

**Por quê?**

- **Independência**: Migrations em SQL puro, não acopladas a ORM específico.
- **Controle fino**: Possibilita operações complexas (índices, triggers, functions).
- **Professor seedado**: Uma migration cria o usuário professor no banco, sem dependência de fixtures Python.

```bash
alembic revision -m "Adiciona tabela de cursos"
alembic upgrade head  # Aplica todas as migrations pendentes
```

### 4. Celery + Redis para Background Tasks (em vez de síncrono)

**Por quê?**

- **IA é lenta**: Gerar conteúdo via Groq leva ~2s. Bloquear a requisição HTTP é péssima UX.
- **Solução**: Enfileirar task em Celery, retornar `task_id` imediatamente, cliente consulta resultado via polling.
- **Redis como broker**: Leve, rápido, perfeito para PoC (em produção, seria RabbitMQ).

**Fluxo:**

```
POST /lessons/1/gerar-conteudo
  ↓
LessonService enfileira task em Celery
  ↓
Retorna { "task_id": "xyz123" } imediatamente (HTTP 202)
  ↓
Cliente faz polling: GET /lessons/1/conteudo-pendente
  ↓
Se pronto: retorna conteúdo HTML | Se ainda processando: tenta novamente
  ↓
POST /lessons/1/confirmar-conteudo (salva no banco)
```

**Alternativa rejeitada**: Fazer síncronamente (esperar 2s por requisição) — má experiência, não escalável.

### 5. Groq via OpenAI SDK (em vez de chamadas HTTP diretas)

**Por quê?**

- **Compatibilidade**: OpenAI SDK é padrão na indústria, fácil trocar modelo ou provider.
- **Type-safety**: SDK Python oferece tipos, auto-complete no IDE.
- **Tratamento de erro**: SDK lida com retries, rate-limiting, conexão.

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/...")
response = await client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
)
```

### 6. pdfplumber para extrair texto de PDFs

**Por quê?**

- **Precisão**: Mantém estrutura e layout, melhor que PyPDF ou PDFMiner.
- **Integração simples**: Uma linha extrai todo o texto de um PDF.
- **Sem dependências pesadas**: Não precisa de ImageMagick ou Ghostscript.

```python
import pdfplumber

with pdfplumber.open(pdf_path) as pdf:
    text = "\n".join(page.extract_text() for page in pdf.pages)
```

---

## Metodologia de Desenvolvimento

### TDD — Test Driven Development

**Ciclo**:

1. **Escreve o teste** → deve falhar (red)
2. **Roda pytest** → confirma falha
3. **Implementa mínimo** → faz o teste passar (green)
4. **Refatora se necessário** → sem quebrar testes (refactor)

**Benefício**: Testes são especificação viva, cobertura é automática, refatorações são seguras.

**Exemplo**:

```python
# test_course_service.py (escrito PRIMEIRO)
@pytest.mark.asyncio
async def test_create_course(db: AsyncSession):
    service = CourseService()
    course = await service.create(db, "Python 101", "Linguagem", "Aprenda Python")
    
    assert course.id is not None
    assert course.title == "Python 101"
    assert course.created_at is not None
```

Teste falha (CourseService não existe). Aí implementamos.

```python
# course/service.py (implementação mínima)
class CourseService:
    async def create(self, session: AsyncSession, title: str, category: str, description: str) -> Course:
        course = Course(title=title, category=category, description=description)
        session.add(course)
        await session.commit()
        await session.refresh(course)
        return course
```

Teste passa. Pronto.

### Método Akita

Conjuntos de princípios de simplificidade:

- **Nunca pule etapas**: CRUD antes de features avançadas. Testes antes de código.
- **Uma responsabilidade**: `CourseService` só sabe criar/atualizar cursos. `LessonAiService` só gera conteúdo com IA.
- **Não antecipe funcionalidades**: Se não está no requisito, não implementa. Complexidade só quando necessária.
- **Código simples**: Sem patterns sofisticados. Se duplicação surge, refatora. Se não, deixa como está.
- **Problema? Entenda a causa raiz**: Não gambi. Se teste falha, debugga até a raiz, não só trata o sintoma.

**Resultado**: Código fácil de entender, manutenível, sem overhead desnecessário.

---

## Padrões de Código

### Domain-Driven Design (DDD)

O projeto está organizado por **domínios de negócio**, não por camada técnica:

```
app/
  course/       ← domínio "Curso"
    model.py    ← entidade Course
    schema.py   ← validação de entrada/saída
    repository.py ← acesso a dados
    service.py    ← lógica de negócio
    router.py     ← endpoints HTTP

  lesson/       ← domínio "Aula"
    model.py
    schema.py
    repository.py
    service.py
    ai_service.py ← geração de conteúdo (IA)
    router.py

  shared/       ← código compartilhado
    exception.py  ← exceções customizadas
    schema.py     ← ApiResponse padrão
    redis_client.py
```

**Benefício**: Fácil adicionar novo domínio (ex: "Certificado"). Cada time gerencia seu domínio.

### Repository Pattern

Abstração entre service e database:

```python
# lesson/repository.py
class LessonRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: int) -> Lesson | None:
        result = await self.session.execute(
            select(Lesson).where(Lesson.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, lesson: Lesson) -> Lesson:
        self.session.add(lesson)
        await self.session.commit()
        await self.session.refresh(lesson)
        return lesson
```

Service usa repositório:

```python
# lesson/service.py
class LessonService:
    async def create(self, session: AsyncSession, module_id: int, name: str, content: str) -> Lesson:
        repo = LessonRepository(session)
        lesson = Lesson(module_id=module_id, name=name, content_editor=content)
        return await repo.create(lesson)
```

**Benefício**: Trocar banco de dados sem mexer em service. Testes usam SQLite em memória.

### Separação Request/Response

Schemas distintos para entrada e saída:

```python
# lesson/schema.py

class LessonRequest(BaseModel):
    name: str
    content_editor: str | None = None

class LessonResponse(BaseModel):
    id: int
    module_id: int
    name: str
    content_editor: str | None
    content_html: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

Router usa Request para validar entrada, Response para serializar saída:

```python
# lesson/router.py

@router.post("/modules/{module_id}/lessons")
async def create_lesson(
    module_id: int,
    lesson: LessonRequest,
    session: AsyncSession = Depends(get_session),
) -> LessonResponse:
    service = LessonService()
    created = await service.create(session, module_id, lesson.name, lesson.content_editor)
    return LessonResponse.model_validate(created)
```

**Benefício**: API clara (documentação automática), validação de tipo automática, fácil evoluir requests sem quebrar clients.

### Exceções Customizadas

Tratamento de erro centralizado:

```python
# shared/exception.py

class RecursoNaoEncontradoException(Exception):
    def __init__(self, recurso: str, id: int):
        self.recurso = recurso
        self.id = id

class RegraDeNegocioException(Exception):
    def __init__(self, mensagem: str):
        self.mensagem = mensagem

# Exception handler no app
@app.exception_handler(RecursoNaoEncontradoException)
async def recurso_nao_encontrado_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "sucesso": False,
            "mensagem": f"{exc.recurso} com ID {exc.id} não encontrado",
            "dados": None,
            "timestamp": datetime.now().isoformat(),
        },
    )
```

Service lança exceção, app handler serializa resposta:

```python
# lesson/service.py
async def get_by_id(self, session: AsyncSession, id: int) -> Lesson:
    repo = LessonRepository(session)
    lesson = await repo.find_by_id(id)
    if not lesson:
        raise RecursoNaoEncontradoException("Lesson", id)
    return lesson
```

**Benefício**: Erro consistente em toda API, sem if/else por endpoint.

---

## Stack Detalhado

| Camada | Tecnologia | Por quê |
|---|---|---|
| **Linguagem** | Python 3.12 | Modern syntax, async/await, type hints |
| **Framework Web** | FastAPI | Async-first, performance, OpenAPI automático |
| **Banco de Dados** | PostgreSQL 16 | Production-ready, confiável, escalável |
| **ORM** | SQLAlchemy 2.0 (async) | Type-safe, migrations via Alembic, suporta async |
| **Migrations** | Alembic | SQL puro, independente de ORM |
| **IA** | Groq (llama-3.3-70b) via OpenAI SDK | Grátis, rápido, compatível com OpenAI |
| **PDF** | pdfplumber | Extração de texto precisa |
| **Validação** | Pydantic v2 | Type hints, serialização automática |
| **Background Tasks** | Celery + Redis | Enfileirar operações longas, não bloquear HTTP |
| **Testes** | pytest + pytest-asyncio | Async-aware, fixtures poderosas |
| **Servidor** | Uvicorn | ASGI, async-native |

---

## Fluxo de Desenvolvimento: Exemplo Prático

Vamos implementar um novo endpoint: **"Adicionar um quiz manual"**.

### 1. Entender o requisito

```
POST /modules/{module_id}/quiz
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

### 2. Escrever testes (TDD)

```python
# tests/quiz/test_quiz_service.py

@pytest.mark.asyncio
async def test_create_quiz_with_questions(db: AsyncSession):
    # Setup
    module = Module(name="Module 1", course_id=1)
    db.add(module)
    await db.commit()
    
    # Test
    service = QuizService()
    quiz_data = {
        "questions": [
            {
                "statement": "O que é Python?",
                "points": 1,
                "alternatives": [
                    {"text": "Uma linguagem", "correct": True},
                    {"text": "Um animal", "correct": False},
                ]
            }
        ]
    }
    quiz = await service.create_with_questions(db, module.id, quiz_data)
    
    # Assert
    assert quiz.id is not None
    assert len(quiz.questions) == 1
    assert quiz.questions[0].statement == "O que é Python?"
    assert len(quiz.questions[0].alternatives) == 2
```

Teste falha. Prosseguir.

### 3. Criar schema (Pydantic)

```python
# quiz/schema.py

class AlternativeRequest(BaseModel):
    text: str
    correct: bool

class QuestionRequest(BaseModel):
    statement: str
    points: int
    alternatives: list[AlternativeRequest]

class QuizWithQuestionsRequest(BaseModel):
    questions: list[QuestionRequest]
```

### 4. Implementar service

```python
# quiz/service.py

async def create_with_questions(
    self, session: AsyncSession, module_id: int, quiz_data: dict
) -> Quiz:
    repo = QuizRepository(session)
    
    # Validar que módulo existe
    module_repo = ModuleRepository(session)
    module = await module_repo.find_by_id(module_id)
    if not module:
        raise RecursoNaoEncontradoException("Module", module_id)
    
    # Criar quiz
    quiz = Quiz(module_id=module_id, show_wrong_answers=False)
    quiz = await repo.create(quiz)
    
    # Criar questões e alternativas
    for q_data in quiz_data["questions"]:
        question = Question(
            quiz_id=quiz.id,
            statement=q_data["statement"],
            points=q_data["points"],
        )
        question = await repo.create_question(question)
        
        for alt_data in q_data["alternatives"]:
            alternative = Alternative(
                question_id=question.id,
                text=alt_data["text"],
                correct=alt_data["correct"],
            )
            await repo.create_alternative(alternative)
    
    return quiz
```

### 5. Implementar router

```python
# quiz/router.py

@router.post("/modules/{module_id}/quiz")
async def create_quiz_with_questions(
    module_id: int,
    quiz_data: QuizWithQuestionsRequest,
    session: AsyncSession = Depends(get_session),
) -> QuizResponse:
    service = QuizService()
    quiz = await service.create_with_questions(session, module_id, quiz_data.model_dump())
    return QuizResponse.model_validate(quiz)
```

### 6. Rodar testes

```bash
GROQ_API_KEY=placeholder pytest tests/quiz/test_quiz_service.py::test_create_quiz_with_questions -v
```

✅ Passa.

### 7. Testar manualmente

```bash
curl -X POST http://localhost:8000/modules/1/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "questions": [
      {
        "statement": "O que é Python?",
        "points": 1,
        "alternatives": [
          {"text": "Linguagem", "correct": true},
          {"text": "Animal", "correct": false}
        ]
      }
    ]
  }'
```

Documentação automática em http://localhost:8000/docs ← já atualizado.

---

## Comparação com Java

| Aspecto | Java (Spring Boot) | Python (FastAPI) |
|---|---|---|
| **Framework** | Spring Boot 3.4 | FastAPI 0.115 |
| **Async** | Project Reactor (Mono/Flux) | asyncio (async/await) |
| **ORM** | JPA + Hibernate | SQLAlchemy 2.0 |
| **Migrations** | Flyway | Alembic |
| **IA** | Spring AI + RestTemplate | OpenAI SDK |
| **PDF** | Apache PDFBox | pdfplumber |
| **Validação** | Bean Validation | Pydantic v2 |
| **Background Tasks** | Síncrono (ConcurrentHashMap em memória) | Celery + Redis |
| **Testes** | JUnit 5 + Mockito | pytest + pytest-asyncio |
| **Docs** | SpringDoc Swagger | FastAPI Swagger (built-in) |

**Diferença principal**: Java é síncrono com fila em memória; Python é async-native com Celery + Redis (melhor para escalar).

---

## O Que Não Está Aqui

- **Autenticação**: Propositalmente ignorada. Uma feature futura.
- **Permissões**: Sem controle de acesso. Todos os endpoints acessíveis.
- **Frontend**: Backend-only. Use Swagger, Postman, ou curl.
- **Cache sofisticado**: Redis só para background tasks.
- **Search avançado**: Sem Elasticsearch ou similares.

---

## Estatísticas

- **61 testes unitários** cobrindo todos os serviços
- **5 domínios** (Course, Module, Lesson, Quiz, shared)
- **15+ endpoints** REST
- **~2000 linhas** de código (sem testes)

---

## Referências

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Celery](https://docs.celeryproject.org/)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [pytest](https://docs.pytest.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Groq API](https://console.groq.com)

---

## Autor

**Aglayrton Julião**  
Desenvolvido com assistência de IA (Claude) usando metodologia TDD + Método Akita.
