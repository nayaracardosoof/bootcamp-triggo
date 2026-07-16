# Q&A Técnico — Research Report Agent

Arquivo de apoio para apresentação do projeto. A ideia é você conseguir responder perguntas técnicas sobre o que foi feito, por que foi feito assim, quais são os limites e como o projeto poderia evoluir.

## 1. Resumo do projeto

### O que é o projeto?

É um agente pesquisador feito com `smolagents` e `Gradio`. Ele recebe uma pergunta ou tema, pesquisa na web com `DuckDuckGoSearchTool` e gera um artefato em Markdown.

O artefato pode ser:

- relatório estruturado;
- resumo rápido;
- comparação;
- plano de ação;
- skill reutilizável.

Além disso, o projeto pode avaliar o artefato gerado usando um `evaluation prompt`.

### Qual problema ele resolve?

Ele transforma uma pesquisa aberta em uma entrega estruturada e reaproveitável. Em vez de apenas responder como um chatbot, ele gera um documento organizado, com formato previsível, e opcionalmente salva esse resultado em `.md`.

### Por que isso é um agente e não só um chatbot?

Porque ele não apenas conversa. Ele usa ferramenta externa de busca, segue um fluxo de execução orientado a tarefa, gera artefatos estruturados e pode chamar uma etapa de avaliação sobre a própria saída.

Fluxo básico:

```text
entrada do usuário
→ seleção ou inferência do modo
→ construção do prompt
→ agente usa ferramenta de busca
→ geração do artefato
→ avaliação opcional
→ exportação opcional em Markdown
```

## 2. Arquitetura

### Como o projeto está organizado?

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
├── README.md
└── QA_TECNICO.md
```

### Qual é a responsabilidade de cada arquivo?

- `app.py`: interface web com Gradio.
- `config.py`: modos disponíveis, profundidades, diretórios e roteamento automático por regras.
- `model_factory.py`: criação/configuração do modelo usado pelos agentes.
- `agents.py`: criação do agente pesquisador e do agente avaliador.
- `prompts.py`: prompts de pesquisa, skill e avaliação.
- `service.py`: orquestra o fluxo principal.
- `storage.py`: salva relatórios e skills em Markdown.

### Por que separar em módulos?

Para deixar o projeto mais fácil de explicar, testar e manter. Se tudo ficasse no `app.py`, interface, prompt, lógica do agente, configuração e exportação ficariam misturados. A separação deixa cada parte com uma responsabilidade clara.

### Qual é o fluxo interno quando o usuário executa uma pesquisa?

```text
1. app.py recebe os dados da interface.
2. app.py chama run_research(...) em service.py.
3. service.py valida a pergunta.
4. Se o modo for Automático, config.py infere o modo por palavras-chave.
5. service.py decide se vai gerar relatório ou skill.
6. prompts.py monta o prompt adequado.
7. agents.py fornece o agente smolagents.
8. O agente executa a tarefa e usa busca web quando necessário.
9. Se avaliação estiver ativa, o agente avaliador avalia o artefato.
10. Se exportação estiver ativa, storage.py salva em .md.
11. app.py exibe resultado, avaliação e arquivo exportado.
```

## 3. Decisões técnicas

### Por que Python?

Python é o ecossistema mais direto para IA generativa, agentes e prototipagem com LLMs. As bibliotecas usadas no projeto também são Python-first: `smolagents`, `gradio`, `python-dotenv` e ferramentas do ecossistema Hugging Face.

Resposta curta para apresentação:

> Usei Python porque ele reduz atrito para criar agentes, integrar ferramentas e publicar no Hugging Face Spaces.

### Por que `smolagents`?

Porque o projeto é alinhado ao curso de Agents da Hugging Face e o `smolagents` é uma biblioteca leve para criar agentes com ferramentas. Ele tem menos abstrações que frameworks maiores e é mais fácil de explicar em um projeto curto.

### Por que não LangChain?

LangChain é poderoso, mas seria mais complexo do que o necessário para este escopo. O projeto não precisava de chains grandes, RAG, memória avançada ou workflows complexos. Para um agente pesquisador simples e explicável, `smolagents` é mais adequado.

### Por que não CrewAI?

CrewAI é mais indicado quando a proposta é ter múltiplos agentes colaborando com papéis diferentes. Aqui o foco é um fluxo simples: pesquisar, sintetizar, gerar artefato e avaliar. Multiagente adicionaria complexidade sem necessidade para o curso.

### Por que Gradio?

Porque permite criar interface rapidamente, aceita Markdown como saída, tem componentes simples e é compatível com Hugging Face Spaces.

### Por que Markdown?

Markdown é simples, legível, versionável e fácil de exportar. Serve bem tanto para relatórios quanto para skills.

### Por que usar `.env`?

Para separar configuração do código. O token da Hugging Face, modelo, diretórios e limites de passos podem mudar por ambiente sem alterar o código.

## 4. smolagents e agentes

### Qual tipo de agente foi usado?

Foi usado `CodeAgent` do `smolagents`.

### O que é um `CodeAgent`?

É um agente que pode raciocinar sobre uma tarefa e usar ferramentas disponíveis para chegar ao resultado. No contexto do projeto, ele usa a ferramenta de busca para coletar informações e depois gera uma resposta estruturada.

### Quantos agentes existem no projeto?

Existem dois papéis principais:

1. agente pesquisador: gera relatório ou skill;
2. agente avaliador: avalia o artefato gerado.

Eles podem usar a mesma infraestrutura de modelo, mas têm prompts e objetivos diferentes.

### Por que criar um agente avaliador separado?

Porque avaliação e geração são tarefas diferentes. O pesquisador tenta resolver a tarefa; o avaliador analisa a qualidade da resposta com uma rubrica específica. Essa separação deixa o fluxo mais claro.

### O agente executa ações perigosas no sistema?

Não foi dado ao agente uma ferramenta para apagar arquivos, rodar comandos arbitrários ou modificar o sistema. A exportação em `.md` é feita pelo código da aplicação, não pelo agente de forma livre.

## 5. Modelo e configuração

### Qual modelo o projeto usa?

O modelo padrão é configurável via `.env`. No projeto, o padrão documentado é:

```env
MODEL_ID=Qwen/Qwen2.5-7B-Instruct
```

Mas pode ser trocado sem alterar código.

### Por que deixar o modelo configurável?

Para permitir testar diferentes modelos conforme disponibilidade, custo ou qualidade. Isso evita acoplar o projeto a um único modelo.

### O que é `MAX_STEPS`?

É o número máximo de passos que o agente pesquisador pode executar. Ele limita tempo, custo e risco de loop.

### O que é `EVALUATION_MAX_STEPS`?

É o número máximo de passos do agente avaliador. Normalmente é menor porque a avaliação não deveria pesquisar novamente, apenas analisar o artefato gerado.

## 6. Busca web

### Qual ferramenta de busca é usada?

`DuckDuckGoSearchTool`, integrada ao `smolagents`.

### Por que DuckDuckGo?

Porque é simples, não exige configuração pesada de API e é suficiente para um projeto de curso.

### Quais são as limitações dessa busca?

- resultados podem variar;
- fontes podem ser incompletas;
- pode retornar páginas desatualizadas;
- não garante validação factual;
- depende de internet e disponibilidade externa.

### Como melhorar isso em uma versão futura?

- priorizar documentação oficial;
- usar APIs de busca com metadados melhores;
- registrar URLs e snippets consultados;
- implementar allowlist de domínios;
- adicionar verificação cruzada de fontes.

## 7. Modos de saída

### Quais modos existem?

- `Automático`;
- `Relatório estruturado`;
- `Resumo rápido`;
- `Comparação`;
- `Plano de ação`;
- `Gerar skill`.

### O que o modo automático faz?

Ele tenta inferir o melhor formato de saída com regras simples por palavras-chave.

Exemplos:

```text
crie uma skill pra code review
→ Gerar skill

compare smolagents e LangChain
→ Comparação

monte um plano para aprender GitHub Actions
→ Plano de ação

resuma agentes de IA em poucas palavras
→ Resumo rápido

pesquise sobre galinhas
→ Relatório estruturado
```

### Por que o modo automático não usa outro LLM classificador?

Porque seria mais lento, mais caro e mais complexo. Para o escopo do curso, regras simples são suficientes, previsíveis e fáceis de explicar. Além disso, o usuário ainda pode escolher o modo manualmente.

Resposta curta para avaliador técnico:

> Eu optei por roteamento determinístico por palavras-chave para reduzir custo e complexidade. Se o projeto evoluísse para produção, eu mediria erros de roteamento e só então avaliaria usar um classificador com LLM.

### Qual a limitação do modo automático?

Ele não entende intenção profunda. Se o usuário pedir algo de forma muito indireta, pode cair no modo padrão. Por isso existe o seletor manual.

## 8. Geração de skills

### O que significa gerar uma skill?

Significa transformar a pesquisa em um documento operacional reutilizável, com passos, entradas, saídas, boas práticas, exemplos e critérios de sucesso.

### Qual é o formato da skill?

Markdown com frontmatter YAML:

```markdown
---
name: nome-curto-da-skill
description: Descrição objetiva da skill em uma frase.
version: 1.0.0
language: pt-BR
---

# Skill: Nome da Skill

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

### Por que Markdown com frontmatter e não JSON?

Porque Markdown é melhor para leitura e apresentação. O frontmatter permite metadados simples sem perder legibilidade. Em uma versão futura, o projeto poderia exportar também JSON para integração com sistemas.

### Como evitar que a skill fique genérica?

O prompt exige seções práticas como entradas, saída, passo a passo, erros comuns, exemplo e critérios de sucesso. Além disso, o evaluation prompt da skill penaliza conteúdo genérico demais.

## 9. Evaluation prompt

### O que é o evaluation prompt?

É um prompt avaliador. Ele recebe o artefato gerado e dá uma avaliação estruturada com nota, pontos fortes, pontos fracos, riscos e sugestões de melhoria.

### Ele faz nova pesquisa?

Não. Ele avalia somente o conteúdo fornecido.

### Por que ele não pesquisa novamente?

Para manter o fluxo simples, rápido e barato. A avaliação atual é qualitativa, não uma verificação factual completa.

### A avaliação garante que a resposta está correta?

Não. Ela ajuda a identificar problemas de clareza, estrutura, fontes e risco de alucinação, mas não garante verdade factual. Para isso, seria necessária uma etapa adicional de verificação externa.

### Quais critérios são avaliados no relatório?

- clareza e organização;
- aderência ao pedido original;
- precisão factual aparente;
- completude;
- utilidade prática;
- tratamento de incertezas;
- fontes e transparência;
- risco de alucinação.

### Quais critérios são avaliados na skill?

- clareza do objetivo;
- reutilização;
- passos práticos;
- exemplos;
- completude;
- precisão técnica aparente;
- limites e incertezas;
- referências;
- risco de genericidade ou alucinação.

### Por que usar um LLM para avaliar outro resultado de LLM?

Porque é uma camada de revisão automática útil, mesmo não sendo perfeita. Ela melhora a transparência e ajuda o usuário a perceber limitações do artefato.

## 10. Exportação

### Onde relatórios são salvos?

Na pasta configurada por:

```env
REPORTS_DIR=reports
```

### Onde skills são salvas?

Na pasta configurada por:

```env
GENERATED_SKILLS_DIR=generated_skills
EVALUATIONS_DIR=evaluations
```

### Por que salvar em arquivo local?

Porque é simples e suficiente para o projeto. O usuário pode baixar, revisar, versionar ou compartilhar o Markdown.

### Por que não usar banco de dados?

Banco adicionaria complexidade sem necessidade. Para o objetivo de gerar artefatos, arquivos `.md` resolvem bem.

## 11. Segurança e confiabilidade

### Quais são os principais riscos?

- alucinação do modelo;
- fontes incorretas ou desatualizadas;
- prompt injection vindo de páginas pesquisadas;
- avaliação automática falhar em detectar erro;
- dependência de APIs externas;
- indisponibilidade do modelo.

### Como o projeto reduz alucinação?

- prompts pedem para não inventar fatos;
- prompts pedem fontes quando habilitado;
- prompts pedem declaração de incerteza;
- avaliação aponta afirmações sem suporte;
- saída estruturada facilita revisão humana.

### O projeto elimina alucinação?

Não. Ele reduz riscos e torna problemas mais visíveis, mas revisão humana ainda é importante em decisões críticas.

### Existe risco de prompt injection?

Sim, como qualquer agente que lê conteúdo externo. O risco é reduzido porque o agente tem poucas ferramentas e não possui ferramentas destrutivas. Em produção, eu adicionaria filtros de fonte, sanitização de conteúdo e regras mais fortes para tratar conteúdo externo como dados, não instruções.

### O token da Hugging Face fica seguro?

O projeto usa `.env` e `.env.example`. O token real deve ficar fora do Git. Essa é a prática correta para evitar vazamento de credenciais.

## 12. Testes e validação

### Como o projeto foi validado?

Validação básica:

```bash
python -m compileall -q app.py research_report_agent
```

Também foram verificados os builders de prompt e o roteamento automático.

### Isso é suficiente para produção?

Não. Para produção, seria necessário adicionar testes automatizados formais, mocks do agente, dataset de avaliação, logs e monitoramento.

### Como testar o modo automático?

Casos esperados:

```text
pesquise sobre galinhas
→ Relatório estruturado

crie uma skill pra code review
→ Gerar skill

compare smolagents e LangChain
→ Comparação

monte um plano para aprender GitHub Actions
→ Plano de ação

resuma agentes de IA
→ Resumo rápido
```

### Como testar geração de skill?

Executar:

```text
Crie uma skill para code review em projetos Python.
```

Verificar se a saída contém:

- frontmatter;
- objetivo;
- entradas esperadas;
- saída esperada;
- passo a passo;
- exemplo;
- critérios de sucesso.

## 13. Performance e custo

### O que impacta o tempo de resposta?

- modelo escolhido;
- latência da API;
- busca web;
- profundidade escolhida;
- `MAX_STEPS`;
- avaliação ativada.

### A avaliação aumenta custo?

Sim. Ela faz uma segunda execução com o agente avaliador. Por isso é opcional.

### Como reduzir custo?

- usar modelo menor;
- reduzir `MAX_STEPS`;
- desativar avaliação;
- usar profundidade baixa ou média;
- implementar cache no futuro.

## 14. Limitações conhecidas

### Quais são as limitações principais?

- não há verificação factual completa;
- busca web pode trazer fontes ruins;
- evaluation prompt não garante verdade;
- roteamento automático é baseado em palavras-chave;
- não há histórico persistente;
- não há banco de dados;
- não há cache;
- não há autenticação;
- não há proteção robusta contra prompt injection.

### O que pode dar errado na apresentação?

- `HF_TOKEN` não configurado;
- modelo indisponível;
- internet instável;
- dependência não instalada;
- busca web falhar;
- resposta demorar;
- limite da API.

### Como se preparar?

- testar antes com exemplos curtos;
- deixar `.env` configurado;
- deixar avaliação desligada se precisar de velocidade;
- ter um relatório e uma skill exportados como backup;
- preparar explicação da arquitetura.

## 15. Perguntas difíceis e respostas prontas

### Se o agente pode alucinar, por que confiar nele?

Não devemos confiar cegamente. O projeto organiza pesquisa e síntese, mas deixa claro que fontes e incertezas precisam ser consideradas. O evaluation prompt ajuda a apontar riscos, dá nota e sugere melhorias, mas revisão humana continua importante.

### O evaluation prompt não é só outro LLM opinando?

Sim, ele é uma avaliação automatizada, não uma prova formal. O objetivo é detectar problemas de estrutura, completude, falta de fontes e riscos aparentes. Para validação factual forte, eu adicionaria verificação independente.

### Por que não usar RAG?

Porque o projeto pesquisa na web aberta. RAG faria mais sentido se eu tivesse uma base documental controlada, como PDFs, documentação interna ou base de conhecimento própria.

### Por que não usar banco de dados?

Porque o objetivo é gerar artefatos Markdown, não gerenciar histórico multiusuário. Banco de dados seria uma evolução, mas não é necessário para o MVP do curso.

### Por que gerar skill não foge da proposta de pesquisador?

Não foge. A skill é uma forma diferente de sintetizar a pesquisa. Em vez de entregar apenas um relatório, o agente transforma os achados em conhecimento operacional reutilizável.

### Por que não criar um agente separado só para skills?

Para manter o projeto simples. O mesmo agente pesquisador consegue gerar relatório ou skill usando prompts diferentes. Em uma versão maior, poderia existir um agente especializado em skill authoring.

### Como garantir que as fontes são reais?

Hoje o prompt orienta o agente a não inventar fontes. Uma garantia mais forte exigiria capturar URLs da busca, validar links e armazenar snippets consultados. Isso seria uma evolução futura.

### Como levaria isso para produção?

Eu adicionaria autenticação, logs, cache, testes automatizados, validação de fontes, controle de rate limit, persistência, monitoramento e uma política mais forte contra prompt injection.

### Como testaria isso com LLM sendo não determinístico?

Separaria testes determinísticos e testes de contrato. Determinísticos: roteamento automático, builders de prompt e exportação. Contratos: saída não vazia, presença de seções obrigatórias, frontmatter em skills e nota na avaliação.

### Qual foi o principal trade-off?

Simplicidade versus sofisticação. Eu preferi um projeto claro, demonstrável e fácil de explicar, em vez de adicionar RAG, multiagentes, banco de dados e classificador por LLM.

## 16. Evoluções futuras

### O que você melhoraria primeiro?

1. testes automatizados;
2. cache de pesquisas;
3. validação de fontes;
4. exportação JSON para skills;
5. histórico de relatórios;
6. avaliação factual opcional;
7. separação entre modelo gerador e modelo avaliador;
8. suporte a upload de documentos;
9. RAG para bases controladas;
10. logs estruturados.

### Quando faria sentido usar um LLM classificador?

Quando o modo automático por regras começasse a errar com frequência. Antes disso, eu coletaria exemplos de erro e avaliaria se o ganho compensa custo e latência.

### Quando faria sentido multiagente?

Quando a tarefa exigir papéis realmente diferentes, como pesquisador, verificador factual, redator e revisor. Para este MVP, isso seria complexidade extra.

## 17. Respostas curtas para decorar

### Explique o projeto em uma frase.

É um agente com `smolagents` que pesquisa na web e transforma o resultado em relatórios ou skills Markdown, com avaliação opcional da qualidade.

### Por que `smolagents`?

Porque é leve, direto, alinhado ao curso da Hugging Face e facilita criar agentes com ferramentas.

### Por que Python?

Porque é o ecossistema mais maduro para IA generativa e permite integrar `smolagents`, `Gradio` e Hugging Face com pouco atrito.

### Por que Gradio?

Porque cria uma interface funcional rapidamente e é fácil de publicar no Hugging Face Spaces.

### Por que Markdown?

Porque é simples, legível, versionável e adequado para relatórios e skills.

### Qual a maior limitação?

A qualidade factual depende das fontes e do modelo. O evaluation prompt ajuda, mas não garante correção absoluta.

### Qual a principal decisão técnica?

Manter uma arquitetura simples e modular, com roteamento automático por regras em vez de adicionar outro LLM classificador.

## 18. Roteiro de apresentação

### Demonstração sugerida

1. Abrir o app.
2. Mostrar o modo `Automático`.
3. Executar:

```text
pesquise sobre galinhas
```

4. Mostrar que gera relatório.
5. Executar:

```text
crie uma skill pra code review em projetos Python
```

6. Mostrar que gera skill.
7. Ativar exportação `.md`.
8. Mostrar arquivo salvo.
9. Mostrar evaluation prompt e explicar que é uma revisão automática, não garantia factual.

### Explicação técnica curta

> A interface chama uma função de serviço. O serviço resolve o modo, monta o prompt correto, executa o agente de pesquisa com ferramenta de busca e, opcionalmente, chama um agente avaliador com uma rubrica. Se o usuário quiser, o resultado é salvo em Markdown como relatório ou skill.

### Frase para justificar o escopo

> Eu preferi um MVP simples e explicável porque o objetivo do curso é demonstrar agentes com ferramenta, geração de artefato e avaliação. Evitei adicionar RAG, banco de dados ou multiagentes porque isso aumentaria a complexidade sem ser necessário para o objetivo principal.
 