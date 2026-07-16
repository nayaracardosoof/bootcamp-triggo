from research_report_agent.config import SKILL_MODE
from research_report_agent.prompts import (
    build_evaluation_prompt,
    build_research_prompt,
    build_skill_evaluation_prompt,
    build_skill_prompt,
)


def test_build_research_prompt_contains_expected_context():
    prompt = build_research_prompt(
        question="pesquise sobre galinhas",
        mode="Relatório estruturado",
        depth="Média",
        include_sources=True,
    )

    assert "pesquise sobre galinhas" in prompt
    assert "Relatório estruturado" in prompt
    assert "Fontes consultadas" in prompt
    assert "português do Brasil" in prompt


def test_build_skill_prompt_contains_skill_template():
    prompt = build_skill_prompt(
        question="crie uma skill para code review",
        depth="Alta",
        include_sources=True,
    )

    assert "crie uma skill para code review" in prompt
    assert SKILL_MODE in prompt
    assert "# Skill: Nome da Skill" in prompt
    assert "Referências consultadas" in prompt
    assert "somente o Markdown da skill" in prompt
    assert "manifest JSON será criado pelo sistema" in prompt


def test_build_report_evaluation_prompt_contains_report():
    prompt = build_evaluation_prompt(
        question="pergunta original",
        report="# Relatório gerado",
        mode="Resumo rápido",
        depth="Baixa",
        include_sources=False,
    )

    assert "# Avaliação do Relatório" in prompt
    assert "pergunta original" in prompt
    assert "# Relatório gerado" in prompt
    assert "## Veredito curto" in prompt
    assert "## Sugestões de melhoria prioritárias" in prompt
    assert "Fontes solicitadas pelo usuário:\nNão" in prompt


def test_build_skill_evaluation_prompt_contains_skill():
    prompt = build_skill_evaluation_prompt(
        question="pedido original",
        skill="# Skill gerada",
        depth="Média",
        include_sources=True,
    )

    assert "# Avaliação da Skill" in prompt
    assert "pedido original" in prompt
    assert "# Skill gerada" in prompt
    assert "## Veredito curto" in prompt
    assert "## Validação de formato" in prompt
    assert "JSON manifest: será gerado automaticamente pelo app" in prompt
    assert "## Sugestões de melhoria prioritárias" in prompt
    assert "Fontes solicitadas pelo usuário:\nSim" in prompt
 