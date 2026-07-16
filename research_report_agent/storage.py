import json
import re
from datetime import datetime, timezone
from pathlib import Path

from research_report_agent.config import EVALUATIONS_DIR, GAIA_RUNS_DIR, GENERATED_SKILLS_DIR, REPORTS_DIR


def slugify(text: str, max_length: int = 70) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9áàâãéèêíïóôõöúçñ\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = text.strip("-")
    return text[:max_length].strip("-") or "pesquisa"


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_markdown(question: str, content: str, directory: Path, prefix: str) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{_timestamp()}_{prefix}_{slugify(question)}.md"
    file_path = directory / filename
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def save_report(question: str, content: str) -> str:
    return save_markdown(question, content, REPORTS_DIR, "relatorio")


def save_skill(question: str, content: str) -> list[str]:
    """Salva a skill em Markdown e um manifest JSON de carregamento ao lado dela."""
    GENERATED_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = _timestamp()
    slug = slugify(question)
    skill_id = f"{timestamp}_skill_{slug}"

    markdown_path = GENERATED_SKILLS_DIR / f"{skill_id}.md"
    manifest_path = GENERATED_SKILLS_DIR / f"{skill_id}.json"

    markdown_path.write_text(content, encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "type": "skill",
        "id": skill_id,
        "name": slug,
        "description": question.strip(),
        "language": "pt-BR",
        "content_file": markdown_path.name,
        "content_format": "markdown",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return [str(markdown_path), str(manifest_path)]


def save_evaluation(question: str, content: str) -> str:
    return save_markdown(question, content, EVALUATIONS_DIR, "avaliacao")


def save_json_payload(payload: object, directory: Path, prefix: str) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{_timestamp()}_{prefix}.json"
    file_path = directory / filename
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(file_path)


def save_gaia_run(
    submission_payload: dict,
    report_markdown: str,
    submit_result: dict | None = None,
) -> list[str]:
    """Salva os artefatos locais de uma execução GAIA."""
    GAIA_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = _timestamp()

    answers_path = GAIA_RUNS_DIR / f"{timestamp}_gaia_answers.json"
    report_path = GAIA_RUNS_DIR / f"{timestamp}_gaia_report.md"

    answers_path.write_text(
        json.dumps(submission_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(report_markdown, encoding="utf-8")

    file_paths = [str(answers_path), str(report_path)]

    if submit_result is not None:
        result_path = GAIA_RUNS_DIR / f"{timestamp}_gaia_submission_result.json"
        result_path.write_text(
            json.dumps(submit_result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        file_paths.append(str(result_path))

    return file_paths
 