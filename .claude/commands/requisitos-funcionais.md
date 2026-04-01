# Requisitos Funcionais — poc-llm-ufc-simple-py

## Cursos
- **RF01** – Professor cria curso informando título, categoria, descrição e imagem de capa opcional
- **RF02** – Professor lista todos os cursos criados
- **RF03** – Professor visualiza detalhes de um curso

## Módulos
- **RF04** – Professor cria módulos dentro de um curso com nome e imagem de capa opcional
- **RF05** – Professor lista módulos de um curso
- **RF06** – Professor visualiza detalhes de um módulo

## Aulas
- **RF07** – Professor cria aula dentro de um módulo informando nome
- **RF08** – Campo de texto (`content_editor`) e arquivo PDF coexistem na mesma aula
- **RF09** – Professor lista aulas de um módulo
- **RF10** – Professor visualiza detalhes de uma aula

## Conteúdo da Aula — Manual
- **RF11** – Professor digita conteúdo diretamente no campo `content_editor` (texto livre)

## Conteúdo da Aula — IA
- **RF12** – Professor solicita geração de conteúdo pela IA a partir de:
  - texto digitado (`content_editor`), ou
  - arquivo PDF enviado
- **RF13** – Conteúdo gerado fica em memória aguardando decisão (não salvo no banco)
- **RF14** – Professor confirma → conteúdo é persistido no banco em `content_editor`
- **RF15** – Professor solicita regerar → novo conteúdo sobrescreve o anterior pendente em memória
- **RF16** – Professor ignora → conteúdo pendente descartado (não confirma, sem endpoint)

## Quiz — Manual
- **RF17** – Professor cria quiz já com perguntas e alternativas no body (não existe quiz vazio)
- **RF18** – Professor adiciona perguntas ao quiz manualmente após a criação
- **RF19** – Professor adiciona alternativas a cada pergunta, marcando qual é a correta
- **RF20** – Cada pergunta deve ter mínimo de 2 alternativas e exatamente 1 correta
- **RF21** – Professor configura exibição do quiz: mostrar gabarito, mostrar erros, mostrar pontuação

## Quiz — IA
- **RF22** – Professor solicita geração de quiz pela IA; a IA lê o conteúdo de todas as aulas do módulo
- **RF23** – Professor define quantidade de perguntas (padrão: 5) via parâmetro `quantidade`
- **RF24** – Quiz gerado retorna para visualização aguardando decisão (não salvo no banco)
- **RF25** – Quiz gerado pela IA já inclui qual alternativa é a correta em cada pergunta
- **RF26** – Professor confirma → quiz é persistido no banco (perguntas + alternativas + corretas)
- **RF27** – Professor solicita regerar → novo quiz sobrescreve o anterior pendente em memória
- **RF28** – Professor ignora → quiz pendente descartado (não confirma, sem endpoint)
- **RF29** – Se não houver conteúdo legível nas aulas: retorna 422 com mensagem clara
