# poc-llm-ufc-simple-py — Briefing do Projeto

## O que é
PoC simplificada de uma plataforma LMS com IA embarcada.
Sem segurança, sem autenticação — foco total no fluxo de criação de conteúdo com IA.
Professor único seedado via Alembic. Sem login, sem token.

## Stack
Python 3.12 · FastAPI · PostgreSQL 16 · Alembic · SQLAlchemy
Groq via openai SDK (llama-3.3-70b-versatile) · pdfplumber
Pydantic v2 · pytest · Uvicorn

## Modelo de Dados
```
Course    (1) ──> (N) Module
Module    (1) ──> (N) Lesson
Module    (1) ──> (0..1) Quiz
Quiz      (1) ──> (N) Question
Question  (1) ──> (N) Alternative
```

## Estrutura de Módulos
```
app
  course    → router · service · repository · model · schema · exception
  module    → router · service · repository · model · schema · exception
  lesson    → router · service · repository · model · schema · exception
  quiz      → router · service · repository · model · schema · exception
  shared    → config · schema · exception
```

## Convenções de Código
- Idioma: inglês para entidades, campos, métodos e variáveis
- Módulo raiz: `app`
- Schemas separados: `XxxRequest` (entrada) e `XxxResponse` (saída)
- Todos os models possuem `created_at` e `updated_at`
- Resposta padrão da API:
  ```json
  { "sucesso": true, "mensagem": "", "dados": {}, "timestamp": "" }
  ```
- Commits em português no imperativo: `"Adiciona endpoint de criação de curso"`

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

## Comandos Disponíveis
```
/arquitetura            → entidades, tabelas SQL, endpoints REST
/regras-negocio         → regras de negócio do sistema
/requisitos-funcionais  → requisitos funcionais da PoC
```
