# Regras de Negócio — poc-llm-ufc-simple-py

- **RN01** – Professor único no sistema, seedado via Alembic; sem cadastro ou autenticação
- **RN02** – Pergunta deve ter mínimo de 2 alternativas e exatamente 1 marcada como correta
- **RN03** – Arquivo aceito nas aulas: somente PDF (`application/pdf`)
- **RN04** – Conteúdo gerado pela IA não é persistido automaticamente; requer confirmação explícita
- **RN05** – Quiz gerado pela IA não é salvo automaticamente; requer confirmação explícita
- **RN06** – Ao regerar conteúdo ou quiz, o resultado anterior é sobrescrito em memória (não no banco)
- **RN07** – Professor pode criar quiz manualmente ou via IA — os dois caminhos são válidos
- **RN08** – Uma aula pode ter conteúdo manual (`content_editor`) e arquivo PDF coexistindo
- **RN09** – Um módulo pode ter no máximo um quiz (1:1); tentar criar segundo retorna 422
- **RN10** – Se não houver conteúdo legível nas aulas do módulo, a geração de quiz via IA retorna 422
- **RN11** – Quiz manual deve ser criado já com perguntas e alternativas; não existe criação de quiz vazio
- **RN12** – Imagens de capa (curso e módulo) são validadas por magic bytes; somente `image/*` é aceito
- **RN13** – Imagens e arquivos PDF são armazenados localmente no diretório configurado em `UPLOAD_DIR`
- **RN14** – Conteúdo pendente da IA (aula e quiz) vive em memória (dicionário em memória); não há coluna ativa no banco para este estado
- **RN15** – A API expõe apenas métodos GET e POST; sem PATCH, PUT ou DELETE
