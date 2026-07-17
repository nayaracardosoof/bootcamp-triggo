---
title: Research Report Agent
emoji: 🔎
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# Research Report Agent

Agente pesquisador feito com `smolagents` e `Gradio`.

Ele recebe uma pergunta ou tema, pesquisa na web com DuckDuckGo e gera um artefato em Markdown. O usuário pode gerar:

1. um relatório de pesquisa;
2. uma skill reutilizável; ou
3. executar o modo GAIA para benchmark/submissão no avaliador da Hugging Face.

Opcionalmente, o projeto também avalia o artefato gerado com um **evaluation prompt**.

## O que o projeto faz

- Pesquisa informações na web usando `DuckDuckGoSearchTool`.
- Usa `CodeAgent` do `smolagents` para conduzir a tarefa.
- Gera respostas em Markdown.
- Tem modo `Automático` para inferir o formato de saída por regras simples.
- Permite escolher manualmente o tipo de saída:
  - relatório estruturado;
  - resumo rápido;
  - comparação;
  - plano de ação;
  - gerar skill.
- Permite escolher profundidade:
  - baixa;
  - média;
  - alta.
- Pode incluir fontes ou referências consultadas.
- Pode avaliar automaticamente a qualidade do resultado.
- Pode exportar relatórios em `.md` na pasta `reports/`.
- Pode exportar skills em `.md` com manifest `.json` na pasta `generated_skills/` e avaliações separadas em `evaluations/`.
- Tem modo GAIA para buscar tarefas, gerar respostas curtas, validar payload e salvar submissões em `gaia_runs/`.

## Modo automático

O modo `Automático` é o padrão da interface.

Ele não usa outro LLM para classificar a intenção. A inferência é feita com regras simples por palavras-chave, para manter o projeto leve e fácil de explicar.

Regras principais:

```text
"crie uma skill", "gere uma skill", "skill para", "skill pra"
→ Gerar skill

"compare", "diferença entre", "versus", "vs"
→ Comparação

"plano", "passo a passo", "roadmap", "como fazer", "como implementar"
→ Plano de ação

"resuma", "resumo", "explique rapidamente", "em poucas palavras"
→ Resumo rápido

caso contrário
→ Relatório estruturado
```

Exemplos:

```text
pesquise sobre galinhas
→ Relatório estruturado
```

```text
crie uma skill pra code review
→ Gerar skill
```

```text
compare smolagents e LangChain
→ Comparação
```

O usuário ainda pode escolher manualmente qualquer modo se quiser controlar o formato da saída.

## Fluxos disponíveis

### 1. Relatório de pesquisa

Use quando quiser pesquisar, entender, comparar ou transformar um tema em plano de ação.

Fluxo:

```text
pergunta do usuário
→ inferência do modo, se estiver em Automático
→ pesquisa web
→ síntese dos achados
→ relatório em Markdown
→ avaliação opcional
→ exportação opcional em reports/
```

Exemplo:

```text
Compare smolagents, LangChain e CrewAI para criar um agente pesquisador simples.
```

Saída esperada:

```text
# Relatório de Pesquisa

## Pergunta original
## Resumo executivo
## Subperguntas investigadas
## Principais achados
## Comparação das fontes
## Recomendação prática
## Fontes consultadas
```

### 2. Geração de skill

Use quando quiser que o agente pesquise um tema e transforme os achados em uma skill prática e reutilizável.

Fluxo:

```text
pedido do usuário
→ inferência do modo, se estiver em Automático
→ pesquisa web
→ extração de conhecimento operacional
→ skill em Markdown
→ avaliação específica da skill
→ exportação opcional em generated_skills/
```

Exemplo:

```text
Crie uma skill para code review em projetos Python.
```

Saída esperada:

```text
---
name: code-review-python
description: Skill para revisar código Python de forma estruturada.
version: 1.0.0
language: pt-BR
---

# Skill: Code Review em Python

## Objetivo
## Quando usar
## Entradas esperadas
## Saída esperada
## Pré-requisitos
## Passo a passo operacional
## Boas práticas
## Erros comuns
## Exemplo de uso
## Critérios de sucesso
## Referências consultadas
```


### 3. Modo GAIA / Hugging Face

Use quando quiser rodar o agente contra o avaliador GAIA do Hugging Face Agents Course.

Fluxo:

```text
endpoint /questions
→ agente resolve cada tarefa
→ normalização da resposta final curta
→ retry automático quando a validação detectar resposta ruim
→ revisão automática de formato antes do envio
→ validação estática do payload
→ salvamento em gaia_runs/
→ submissão opcional para /submit
```

Arquivos gerados localmente:

```text
gaia_runs/
  *_gaia_answers.json
  *_gaia_report.md
  *_gaia_submission_result.json  # somente quando submeter remotamente
```

O JSON de respostas segue o formato:

```json
{
  "username": "seu-usuario",
  "agent_code": "https://huggingface.co/spaces/seu-usuario/seu-space",
  "answers": [
    {
      "task_id": "abc123",
      "submitted_answer": "Paris"
    }
  ]
}
```

Regras importantes para GAIA:

- `submitted_answer` deve ser curta e exata.
- Não envie relatório, Markdown ou explicação no campo de resposta.
- Preencha `username` e `agent_code` antes de submeter ao avaliador remoto.
- Rode primeiro sem marcar envio remoto para conferir os arquivos locais.
- O sistema tenta novamente respostas inválidas ou fracas antes de salvar/submeter.
- A revisão automática só deve limpar formato; ela não deve trocar o conteúdo factual da resposta.

## Evaluation prompt

O evaluation prompt é um prompt avaliador. Ele não faz uma nova pesquisa; ele analisa o artefato gerado.

O projeto tem dois tipos de avaliação.

### Avaliação de relatório

Avalia:

- clareza e organização;
- aderência ao pedido original;
- precisão factual aparente;
- completude;
- utilidade prática;
- tratamento de incertezas;
- transparência das fontes;
- risco de alucinação.

### Avaliação de skill

Avalia:

- clareza do objetivo;
- reutilização por outro agente ou pessoa;
- passos práticos;
- qualidade dos exemplos;
- completude da estrutura;
- precisão técnica aparente;
- tratamento de limites;
- referências;
- risco de conteúdo genérico ou alucinado.

Os prompts ficam em:

```text
research_report_agent/prompts.py
```

## Estrutura do projeto

```text
.
├── app.py
├── research_report_agent/
│   ├── __init__.py
│   ├── agents.py
│   ├── config.py
│   ├── model_factory.py
│   ├── prompts.py
│   ├── service.py
│   └── storage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Arquivos principais

### `app.py`

Contém a interface Gradio.

### `research_report_agent/config.py`

Centraliza configurações, modos, profundidades, variáveis de ambiente e regras do modo automático.

### `research_report_agent/model_factory.py`

Cria o modelo usado pelo `smolagents`, mantendo compatibilidade com versões que usam `InferenceClientModel` ou `HfApiModel`.

### `research_report_agent/agents.py`

Cria três agentes:

- agente pesquisador/gerador, com `DuckDuckGoSearchTool`;
- agente avaliador, sem ferramentas externas;
- agente GAIA, com busca web e mais passos para resolver tarefas curtas de benchmark.

### `research_report_agent/prompts.py`

Contém:

- comportamento do agente pesquisador;
- template de relatório;
- template de skill;
- evaluation prompt de relatório;
- evaluation prompt de skill;
- funções para montar prompts.

### `research_report_agent/service.py`

Orquestra o fluxo:

```text
entrada → inferência de modo → pesquisa/geração → avaliação opcional → exportação opcional
```

Quando o modo resolvido é `Gerar skill`, salva a skill pura em `generated_skills/`. Se a avaliação estiver ativa, salva o parecer separado em `evaluations/`.
Quando o modo resolvido é relatório, resumo, comparação ou plano de ação, salva em `reports/`.

### `research_report_agent/storage.py`

Cuida da criação de nomes de arquivo e salvamento dos artefatos em Markdown/JSON.

### `research_report_agent/gaia.py`

Implementa o modo GAIA: busca perguntas, baixa anexos quando existirem, executa o agente, normaliza respostas, valida a submissão e opcionalmente envia para o avaliador remoto.

### `research_report_agent/static_grader.py`

Valida objetivamente skills, relatórios Markdown, manifests JSON e respostas/submissões GAIA.

## Requisitos

- Python 3.10 ou superior.
- Conta na Hugging Face.
- Token da Hugging Face para usar modelos via API.

## Instalação local

Crie um ambiente virtual, se desejar:

```bash
python -m venv .venv
```

No Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

No Git Bash:

```bash
source .venv/Scripts/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Configuração

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Edite `.env`:

```env
HF_TOKEN=hf_seu_token_aqui
MODEL_ID=Qwen/Qwen2.5-7B-Instruct
MAX_STEPS=8
EVALUATION_MAX_STEPS=4
GAIA_MAX_STEPS=12
GAIA_MAX_RETRIES=2
GAIA_API_BASE_URL=https://agents-course-unit4-scoring.hf.space
REPORTS_DIR=reports
GENERATED_SKILLS_DIR=generated_skills
EVALUATIONS_DIR=evaluations
GAIA_RUNS_DIR=gaia_runs
```

Também é possível definir variáveis diretamente no terminal.

PowerShell:

```powershell
$env:HF_TOKEN="hf_seu_token_aqui"
$env:MODEL_ID="Qwen/Qwen2.5-7B-Instruct"
```

Git Bash:

```bash
export HF_TOKEN="hf_seu_token_aqui"
export MODEL_ID="Qwen/Qwen2.5-7B-Instruct"
```

## Executar

```bash
python app.py
```

Depois acesse a URL exibida pelo Gradio, normalmente:

```text
http://127.0.0.1:7860
```

## Como usar

### Para gerar relatório

1. Informe a pergunta ou tema.
2. Use `Automático` ou escolha manualmente um modo como `Relatório estruturado`, `Comparação` ou `Plano de ação`.
3. Escolha a profundidade.
4. Marque se quer fontes.
5. Marque se quer avaliação.
6. Marque exportação se quiser salvar `.md` em `reports/`.

### Para gerar skill

1. Informe o tema da skill.
2. Use `Automático` com uma frase como `crie uma skill...` ou escolha manualmente o modo `Gerar skill`.
3. Escolha a profundidade.
4. Marque se quer referências.
5. Marque se quer avaliação.
6. Marque exportação se quiser salvar `.md` em `generated_skills/`.

## Publicar no Hugging Face Spaces

Este projeto já possui o cabeçalho esperado para Spaces no `README.md`.

Passos gerais:

1. Crie um novo Space no Hugging Face.
2. Escolha SDK `Gradio`.
3. Envie os arquivos do projeto.
4. Configure o segredo `HF_TOKEN` nas configurações do Space.
5. Aguarde o build.

Arquivos mínimos necessários:

```text
app.py
research_report_agent/
requirements.txt
README.md
```

## Exemplos de uso

```text
Pesquise sobre galinhas.
```

```text
Compare smolagents, LangChain e CrewAI para criar um agente pesquisador simples.
```

```text
Como publicar um app Gradio no Hugging Face Spaces?
```

```text
Crie uma skill para code review em projetos Python.
```

```text
Crie uma skill sobre GitHub Actions.
```

## Observações importantes

- O agente depende de busca web, então os resultados podem variar.
- O modo automático é baseado em regras simples; se ele inferir errado, escolha o modo manualmente.
- O evaluation prompt ajuda a revisar qualidade, mas também pode errar.
- Informações importantes devem ser validadas manualmente.
- O modo de profundidade alta pode consumir mais tempo e chamadas ao modelo.
- Ativar avaliação executa uma segunda chamada ao modelo.
- A pasta `reports/` é criada apenas quando exportar relatórios.
- A pasta `generated_skills/` é criada apenas quando exportar skills. A pasta `evaluations/` é criada apenas quando exportar com avaliação ativa.
- A pasta `gaia_runs/` é criada apenas quando executar o modo GAIA com salvamento local.

## Dependências principais

- `smolagents`: criação dos agentes.
- `gradio`: interface web.
- `duckduckgo-search`: backend usado pela ferramenta de busca.
- `python-dotenv`: leitura de variáveis do arquivo `.env`.

## Possíveis melhorias futuras

- Histórico de pesquisas.
- Exportação em PDF.
- CLI dedicada para rodar GAIA fora da interface Gradio.
- Testes automatizados com dataset de avaliação.
- Ranking automático de confiabilidade das fontes.
- Mostrar na interface qual modo foi inferido automaticamente.
- Modo com múltiplos agentes: pesquisador, analista, redator e revisor.
- Integração com RAG para pesquisar em documentos próprios.

## Testes automatizados

O projeto inclui testes simples com pytest para validar partes determinísticas da aplicação, sem chamar o modelo e sem fazer pesquisa web.

Os testes cobrem:

- inferência do modo automático;
- geração dos prompts de relatório, skill e avaliação;
- criação segura de nomes de arquivos;
- salvamento de arquivos Markdown/JSON;
- validação estática de skills, relatórios e submissões GAIA;
- normalização e montagem de payload GAIA.

Para executar:

```bash
python -m pytest -q
```

Resultado esperado:

```text
33 passed
```

Esses testes não avaliam a qualidade semântica das respostas do LLM. Eles validam a lógica local do projeto. A qualidade das respostas é revisada pelo evaluation prompt e por validação humana.
 
