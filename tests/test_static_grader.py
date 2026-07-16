import json
from pathlib import Path

from research_report_agent.static_grader import (
    extract_frontmatter,
    validate_report_markdown,
    validate_skill_manifest,
    validate_skill_markdown,
)


VALID_SKILL = """---
name: code-review-python
description: Skill para revisar código Python de forma estruturada.
version: 1.0.0
language: pt-BR
---

# Skill: Code Review em Python

## Objetivo
Revisar código Python com foco em clareza, segurança e manutenção.

## Quando usar
Use antes de aprovar pull requests.

## Entradas esperadas
- Diff ou arquivos alterados.
- Contexto da mudança.

## Saída esperada
Um parecer objetivo com problemas, riscos e sugestões.

## Pré-requisitos
Conhecimento básico de Python e do projeto revisado.

## Passo a passo operacional
1. Leia o objetivo da mudança.
2. Revise os arquivos alterados.
3. Liste achados por prioridade.

## Boas práticas
- Cite arquivos e linhas quando possível.
- Separe problemas reais de preferências pessoais.

## Erros comuns
- Ignorar testes.
- Sugerir mudanças sem impacto claro.

## Exemplo de uso
Entrada: diff de um PR. Saída: checklist de revisão.

## Critérios de sucesso
- Achados são acionáveis.
- Riscos principais foram identificados.

## Referências consultadas
- Não foram listadas fontes externas.
"""


VALID_REPORT = """# Relatório de Pesquisa

## Pergunta original
Pesquise sobre agentes.

## Resumo executivo
Agentes combinam modelo, ferramentas e instruções.

## Principais achados
- Ferramentas ampliam capacidades.
- Avaliação melhora confiabilidade.

## Recomendação prática
Comece com fluxo simples e adicione validação.

## Fontes consultadas
- https://example.com
"""


def test_extract_frontmatter_reads_simple_yaml_metadata():
    frontmatter, body, errors = extract_frontmatter(VALID_SKILL)

    assert errors == []
    assert frontmatter["name"] == "code-review-python"
    assert frontmatter["version"] == "1.0.0"
    assert body.startswith("# Skill: Code Review")


def test_validate_skill_markdown_accepts_valid_skill():
    result = validate_skill_markdown(VALID_SKILL)

    assert result.valid is True
    assert result.score == 10
    assert result.errors == []
    assert result.metadata["frontmatter"]["language"] == "pt-BR"


def test_validate_skill_markdown_rejects_missing_frontmatter_and_sections():
    result = validate_skill_markdown("# Skill: Incompleta\n\n## Objetivo\nAlgo curto.")

    assert result.valid is False
    assert any("Frontmatter YAML ausente" in error for error in result.errors)
    assert any("Campo obrigatório ausente" in error for error in result.errors)
    assert any("Seção obrigatória ausente" in error for error in result.errors)


def test_validate_skill_markdown_rejects_manifest_inside_markdown():
    skill_with_json = VALID_SKILL + '\n```json\n{"type": "skill"}\n```\n'

    result = validate_skill_markdown(skill_with_json)

    assert result.valid is False
    assert any("JSON/manifest" in error for error in result.errors)


def test_validate_report_markdown_accepts_valid_report_with_sources():
    result = validate_report_markdown(VALID_REPORT, require_sources=True)

    assert result.valid is True
    assert result.errors == []


def test_validate_report_markdown_requires_sources_when_requested():
    report_without_sources = "# Relatório\n\n## Resumo executivo\nTexto.\n\n## Principais achados\nTexto.\n\n## Recomendação prática\nTexto."

    result = validate_report_markdown(report_without_sources, require_sources=True)

    assert result.valid is False
    assert any("Fontes foram solicitadas" in error for error in result.errors)


def test_validate_report_markdown_rejects_unclosed_code_fence():
    result = validate_report_markdown("# Relatório\n\n```python\nprint('oi')")

    assert result.valid is False
    assert any("Bloco de código" in error for error in result.errors)


def test_validate_skill_manifest_accepts_generated_manifest(tmp_path: Path):
    markdown_path = tmp_path / "skill.md"
    manifest_path = tmp_path / "skill.json"
    markdown_path.write_text(VALID_SKILL, encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "type": "skill",
                "id": "skill",
                "name": "code-review-python",
                "description": "Skill para revisar código Python.",
                "language": "pt-BR",
                "content_file": markdown_path.name,
                "content_format": "markdown",
                "created_at": "2026-07-16T10:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    result = validate_skill_manifest(manifest_path, markdown_path)

    assert result.valid is True
    assert result.errors == []


def test_validate_skill_manifest_rejects_invalid_json(tmp_path: Path):
    manifest_path = tmp_path / "skill.json"
    manifest_path.write_text("{invalid", encoding="utf-8")

    result = validate_skill_manifest(manifest_path)

    assert result.valid is False
    assert any("Manifest JSON inválido" in error for error in result.errors)
 