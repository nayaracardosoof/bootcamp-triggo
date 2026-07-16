from research_report_agent.agents import get_evaluation_agent, get_research_agent
from research_report_agent.config import AUTO_MODE, SKILL_MODE, infer_mode_from_question
from research_report_agent.prompts import (
    build_evaluation_prompt,
    build_research_prompt,
    build_skill_evaluation_prompt,
    build_skill_prompt,
)
from research_report_agent.storage import save_report, save_skill


def run_research(
    question: str,
    mode: str,
    depth: str,
    include_sources: bool,
    export_markdown: bool,
    evaluate_response: bool,
):
    question = (question or "").strip()
    if not question:
        return "Informe uma pergunta ou tema para pesquisar.", "", None

    try:
        resolved_mode = infer_mode_from_question(question) if mode == AUTO_MODE else mode
        is_skill_mode = resolved_mode == SKILL_MODE

        if is_skill_mode:
            prompt = build_skill_prompt(question, depth, include_sources)
            artifact = str(get_research_agent().run(prompt)).strip()

            evaluation = ""
            if evaluate_response:
                evaluation_prompt = build_skill_evaluation_prompt(
                    question=question,
                    skill=artifact,
                    depth=depth,
                    include_sources=include_sources,
                )
                evaluation = str(get_evaluation_agent().run(evaluation_prompt)).strip()

            exported_content = artifact if not evaluation else f"{artifact}\n\n---\n\n{evaluation}"
            file_path = save_skill(question, exported_content) if export_markdown else None
            return artifact, evaluation, file_path

        prompt = build_research_prompt(question, resolved_mode, depth, include_sources)
        artifact = str(get_research_agent().run(prompt)).strip()

        evaluation = ""
        if evaluate_response:
            evaluation_prompt = build_evaluation_prompt(
                question=question,
                report=artifact,
                mode=resolved_mode,
                depth=depth,
                include_sources=include_sources,
            )
            evaluation = str(get_evaluation_agent().run(evaluation_prompt)).strip()

        exported_content = artifact if not evaluation else f"{artifact}\n\n---\n\n{evaluation}"
        file_path = save_report(question, exported_content) if export_markdown else None
        return artifact, evaluation, file_path

    except Exception as exc:
        error_message = (
            "Ocorreu um erro ao executar o agente.\n\n"
            f"Detalhes: `{type(exc).__name__}: {exc}`\n\n"
            "Verifique se o `HF_TOKEN` está configurado, se há acesso ao modelo escolhido "
            "e se as dependências foram instaladas."
        )
        return error_message, "", None
 