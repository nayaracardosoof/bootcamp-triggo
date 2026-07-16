from research_report_agent.config import (
    AUTO_MODE,
    SKILL_MODE,
    infer_mode_from_question,
)


def test_auto_mode_constants():
    assert AUTO_MODE == "Automático"
    assert SKILL_MODE == "Gerar skill"


def test_infer_skill_mode():
    assert infer_mode_from_question("crie uma skill pra code review") == SKILL_MODE
    assert infer_mode_from_question("Gere uma skill sobre GitHub Actions") == SKILL_MODE


def test_infer_comparison_mode():
    assert infer_mode_from_question("compare smolagents e LangChain") == "Comparação"
    assert infer_mode_from_question("qual a diferença entre CrewAI e LangGraph?") == "Comparação"


def test_infer_action_plan_mode():
    assert infer_mode_from_question("monte um plano para aprender GitHub Actions") == "Plano de ação"
    assert infer_mode_from_question("como implementar um agente pesquisador?") == "Plano de ação"


def test_infer_summary_mode():
    assert infer_mode_from_question("resuma agentes de IA em poucas palavras") == "Resumo rápido"


def test_infer_default_report_mode():
    assert infer_mode_from_question("pesquise sobre galinhas") == "Relatório estruturado"
    assert infer_mode_from_question("") == "Relatório estruturado"
 