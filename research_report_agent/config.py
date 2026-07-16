import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")
MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))
EVALUATION_MAX_STEPS = int(os.getenv("EVALUATION_MAX_STEPS", "4"))
GAIA_MAX_STEPS = int(os.getenv("GAIA_MAX_STEPS", "4"))
GAIA_MAX_RETRIES = int(os.getenv("GAIA_MAX_RETRIES", "2"))
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "reports"))
GENERATED_SKILLS_DIR = Path(os.getenv("GENERATED_SKILLS_DIR", "generated_skills"))
EVALUATIONS_DIR = Path(os.getenv("EVALUATIONS_DIR", "evaluations"))
GAIA_RUNS_DIR = Path(os.getenv("GAIA_RUNS_DIR", "gaia_runs"))
GAIA_API_BASE_URL = os.getenv("GAIA_API_BASE_URL", "https://agents-course-unit4-scoring.hf.space")

AUTO_MODE = "Automático"
SKILL_MODE = "Gerar skill"

MODES = {
    AUTO_MODE: "Detecte automaticamente o melhor tipo de saída usando regras simples.",
    "Relatório estruturado": "Gere um relatório completo, organizado e objetivo.",
    "Resumo rápido": "Gere uma resposta curta, direta e prática.",
    "Comparação": "Compare alternativas, destacando diferenças, pontos fortes, limitações e recomendação.",
    "Plano de ação": "Transforme a pesquisa em um plano prático com passos recomendados.",
    SKILL_MODE: "Pesquise o tema e transforme os achados em uma skill reutilizável em Markdown.",
}

DEPTHS = {
    "Baixa": "Faça uma pesquisa enxuta. Use poucas consultas e entregue uma resposta breve.",
    "Média": "Faça uma pesquisa equilibrada. Investigue os pontos principais e sintetize bem.",
    "Alta": "Faça uma pesquisa mais cuidadosa. Decomponha a pergunta, compare fontes e destaque incertezas.",
}


def infer_mode_from_question(question: str) -> str:
    """Infere o modo de saída com regras simples, sem chamada extra para LLM."""
    text = (question or "").lower()

    skill_keywords = (
        "crie uma skill",
        "criar uma skill",
        "gere uma skill",
        "gerar uma skill",
        "monte uma skill",
        "montar uma skill",
        "skill para",
        "skill pra",
        "skill de",
    )
    comparison_keywords = (
        "compare",
        "comparar",
        "comparação",
        "comparacao",
        "diferença entre",
        "diferenca entre",
        "versus",
        " vs ",
        " vs.",
    )
    action_plan_keywords = (
        "plano",
        "passo a passo",
        "roadmap",
        "como fazer",
        "como implementar",
        "como criar",
        "como montar",
        "como publicar",
    )
    summary_keywords = (
        "resuma",
        "resumo",
        "explique rapidamente",
        "em poucas palavras",
        "de forma curta",
        "rapidamente",
    )

    if any(keyword in text for keyword in skill_keywords):
        return SKILL_MODE
    if any(keyword in text for keyword in comparison_keywords):
        return "Comparação"
    if any(keyword in text for keyword in action_plan_keywords):
        return "Plano de ação"
    if any(keyword in text for keyword in summary_keywords):
        return "Resumo rápido"

    return "Relatório estruturado"
 