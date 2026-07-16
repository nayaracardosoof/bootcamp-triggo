from research_report_agent.config import SKILL_MODE
from research_report_agent.service import run_research


class FakeAgent:
    def __init__(self, response: str):
        self.response = response

    def run(self, prompt: str):
        return self.response


VALID_SKILL = """---
name: code-review-python
description: Skill para revisar código Python de forma estruturada.
version: 1.0.0
language: pt-BR
---

# Skill: Code Review em Python

## Objetivo
Revisar código Python.

## Quando usar
Antes de aprovar PRs.

## Entradas esperadas
Diff e contexto.

## Saída esperada
Parecer de revisão.

## Pré-requisitos
Conhecimento de Python.

## Passo a passo operacional
1. Leia o diff.

## Boas práticas
- Priorize riscos reais.

## Erros comuns
- Ignorar testes.

## Exemplo de uso
Revise um PR.

## Critérios de sucesso
Achados acionáveis.

## Referências consultadas
Não listadas.
"""


VALID_REPORT = """# Relatório de Pesquisa

## Resumo executivo
Resumo.

## Principais achados
- Achado.

## Recomendação prática
Faça validação.

## Fontes consultadas
- https://example.com
"""


def test_run_research_includes_static_skill_validation_even_without_model_evaluation(monkeypatch):
    import research_report_agent.service as service

    monkeypatch.setattr(service, "get_research_agent", lambda: FakeAgent(VALID_SKILL))

    artifact, evaluation, file_paths = run_research(
        question="Crie uma skill para code review",
        mode=SKILL_MODE,
        depth="Média",
        include_sources=False,
        export_markdown=False,
        evaluate_response=False,
    )

    assert artifact == VALID_SKILL.strip()
    assert "## Validação estática da Skill" in evaluation
    assert "- Status: válido" in evaluation
    assert file_paths is None


def test_run_research_includes_static_report_validation_even_without_model_evaluation(monkeypatch):
    import research_report_agent.service as service

    monkeypatch.setattr(service, "get_research_agent", lambda: FakeAgent(VALID_REPORT))

    artifact, evaluation, file_paths = run_research(
        question="Pesquise sobre agentes",
        mode="Relatório estruturado",
        depth="Média",
        include_sources=True,
        export_markdown=False,
        evaluate_response=False,
    )

    assert artifact == VALID_REPORT.strip()
    assert "## Validação estática do Markdown" in evaluation
    assert "- Status: válido" in evaluation
    assert file_paths is None
 