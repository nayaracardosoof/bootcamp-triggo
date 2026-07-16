from __future__ import annotations

import json
import mimetypes
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from research_report_agent.agents import get_evaluation_agent, get_gaia_agent
from research_report_agent.config import GAIA_API_BASE_URL, GAIA_MAX_RETRIES, GAIA_RUNS_DIR
from research_report_agent.prompts import build_gaia_answer_prompt, build_gaia_retry_prompt, build_gaia_review_prompt
from research_report_agent.static_grader import validate_gaia_answer, validate_gaia_submission
from research_report_agent.storage import save_gaia_run


@dataclass
class GaiaQuestion:
    """Representa uma tarefa do avaliador GAIA/Hugging Face."""

    task_id: str
    question: str
    file_name: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class GaiaAnswer:
    """Resposta pronta para submissão no formato esperado pelo avaliador."""

    task_id: str
    submitted_answer: str
    question: str = ""
    file_path: str | None = None
    validation: Any | None = None
    attempts: int = 1
    review_applied: bool = False
    raw_answer: str = ""
    validation_history: list[Any] = field(default_factory=list)

    def to_submission_item(self) -> dict[str, str]:
        return {"task_id": self.task_id, "submitted_answer": self.submitted_answer}


def _request_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 60,
) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def fetch_gaia_questions(api_base_url: str = GAIA_API_BASE_URL, timeout: int = 60) -> list[GaiaQuestion]:
    """Busca tarefas no endpoint `/questions` do avaliador.

    O formato mais comum é uma lista de objetos com `task_id`, `question` e,
    opcionalmente, `file_name`. A função também aceita resposta envelopada em
    `{"questions": [...]}` para ser tolerante a pequenas mudanças da API.
    """
    url = _join_url(api_base_url, "/questions")
    response = _request_json(url, timeout=timeout)
    items = response.get("questions", response) if isinstance(response, dict) else response

    if not isinstance(items, list):
        raise ValueError("Endpoint /questions não retornou uma lista de tarefas.")

    questions: list[GaiaQuestion] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        task_id = str(item.get("task_id") or item.get("id") or "").strip()
        question = str(item.get("question") or item.get("Question") or "").strip()
        file_name = item.get("file_name") or item.get("filename") or item.get("file")
        file_name = str(file_name).strip() if file_name else None

        if task_id and question:
            questions.append(GaiaQuestion(task_id=task_id, question=question, file_name=file_name, raw=item))

    return questions


def _safe_filename(name: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return clean or "arquivo"


def _guess_extension(content_type: str | None) -> str:
    if not content_type:
        return ""
    content_type = content_type.split(";", 1)[0].strip().lower()
    return mimetypes.guess_extension(content_type) or ""


def _download_url(url: str, target_path: Path, timeout: int = 120) -> Path:
    request = urllib.request.Request(url, headers={"Accept": "*/*"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type")
        data = response.read()

    if target_path.suffix == "":
        target_path = target_path.with_suffix(_guess_extension(content_type))

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(data)
    return target_path


def download_gaia_file(
    task: GaiaQuestion,
    api_base_url: str = GAIA_API_BASE_URL,
    target_dir: str | Path | None = None,
    timeout: int = 120,
) -> str | None:
    """Baixa o arquivo anexo de uma tarefa, quando existir.

    A API do curso costuma expor arquivos em `/files/{task_id}`. Para ficar mais
    robusto, se houver `file_name`, a função também tenta `/files/{file_name}`.
    """
    if not task.file_name:
        return None

    directory = Path(target_dir) if target_dir else GAIA_RUNS_DIR / "files"
    directory.mkdir(parents=True, exist_ok=True)

    filename = _safe_filename(task.file_name)
    target_path = directory / f"{_safe_filename(task.task_id)}_{filename}"

    candidates = [_join_url(api_base_url, f"/files/{urllib.parse.quote(task.task_id)}")]
    if task.file_name:
        candidates.append(_join_url(api_base_url, f"/files/{urllib.parse.quote(task.file_name)}"))

    last_error: Exception | None = None
    for url in candidates:
        try:
            return str(_download_url(url, target_path, timeout=timeout))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 404:
                continue
            raise
        except urllib.error.URLError as exc:
            last_error = exc
            continue

    if last_error:
        raise RuntimeError(f"Não foi possível baixar anexo da tarefa {task.task_id}: {last_error}")
    return None


def normalize_gaia_answer(answer: str) -> str:
    """Limpa a resposta final para o formato curto esperado pelo GAIA."""
    text = (answer or "").strip()

    fence_match = re.fullmatch(r"```(?:text|markdown|md)?\s*\n(?P<body>.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if fence_match:
        text = fence_match.group("body").strip()

    prefixes = (
        "FINAL ANSWER:",
        "Final answer:",
        "Resposta final:",
        "Resposta:",
        "A resposta é:",
        "A resposta final é:",
    )
    for prefix in prefixes:
        if text.casefold().startswith(prefix.casefold()):
            text = text[len(prefix) :].strip()
            break

    # Se o modelo devolveu poucas linhas, use a última linha não vazia quando ela
    # parece ser a resposta. Isso remove pequenas introduções acidentais.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if 1 < len(lines) <= 3 and all(not line.startswith(('-', '*', '#')) for line in lines):
        text = lines[-1]

    return text.strip().strip('"').strip("'").strip()


def _validation_issues_markdown(validation: Any) -> str:
    issues: list[str] = []
    issues.extend(getattr(validation, "errors", []) or [])
    issues.extend(getattr(validation, "warnings", []) or [])
    if not issues:
        return "Nenhum problema objetivo encontrado."
    return "\n".join(f"- {issue}" for issue in issues)


def _score(validation: Any) -> int:
    return int(getattr(validation, "score", 0) or 0)


def _is_good_gaia_answer(validation: Any) -> bool:
    return bool(getattr(validation, "valid", False)) and _score(validation) >= 9


def review_gaia_answer(
    task: GaiaQuestion,
    candidate_answer: str,
    file_path: str | None = None,
    reviewer_agent: Any | None = None,
) -> tuple[str, Any, bool]:
    """Revisa só o formato da resposta GAIA, sem resolver a tarefa de novo."""
    original = normalize_gaia_answer(candidate_answer)
    original_validation = validate_gaia_answer(original)

    selected_reviewer = reviewer_agent or get_evaluation_agent()
    prompt = build_gaia_review_prompt(
        question=task.question,
        candidate_answer=original,
        file_path=file_path,
        task_id=task.task_id,
    )
    reviewed_raw = str(selected_reviewer.run(prompt)).strip()
    reviewed = normalize_gaia_answer(reviewed_raw)
    reviewed_validation = validate_gaia_answer(reviewed)

    if reviewed == original and reviewed_validation.valid:
        return original, reviewed_validation, False
    if reviewed and reviewed_validation.valid and _score(reviewed_validation) > _score(original_validation):
        return reviewed, reviewed_validation, True

    return original, original_validation, False


def answer_gaia_task(
    task: GaiaQuestion,
    file_path: str | None = None,
    agent: Any | None = None,
    reviewer_agent: Any | None = None,
    max_attempts: int | None = None,
    review: bool = True,
) -> GaiaAnswer:
    """Executa o agente em uma tarefa GAIA com retry e revisão de formato."""
    selected_agent = agent or get_gaia_agent()
    attempts_limit = max(1, int(max_attempts or GAIA_MAX_RETRIES + 1))

    prompt = build_gaia_answer_prompt(task.question, file_path=file_path, task_id=task.task_id)
    best_answer = ""
    best_raw_answer = ""
    best_validation = validate_gaia_answer("")
    best_attempt = 0
    validation_history: list[Any] = []
    review_applied = False

    for attempt in range(1, attempts_limit + 1):
        raw_answer = str(selected_agent.run(prompt)).strip()
        normalized = normalize_gaia_answer(raw_answer)
        validation = validate_gaia_answer(normalized)
        validation_history.append(validation)

        if _score(validation) > _score(best_validation):
            best_answer = normalized
            best_raw_answer = raw_answer
            best_validation = validation
            best_attempt = attempt

        if _is_good_gaia_answer(validation):
            best_answer = normalized
            best_raw_answer = raw_answer
            best_validation = validation
            best_attempt = attempt
            break

        if attempt < attempts_limit:
            prompt = build_gaia_retry_prompt(
                question=task.question,
                file_path=file_path,
                task_id=task.task_id,
                previous_answer=normalized or raw_answer,
                validation_issues=_validation_issues_markdown(validation),
                attempt=attempt + 1,
            )

    if review and best_answer:
        reviewed_answer, reviewed_validation, changed = review_gaia_answer(
            task,
            best_answer,
            file_path=file_path,
            reviewer_agent=reviewer_agent,
        )
        validation_history.append(reviewed_validation)
        if _score(reviewed_validation) >= _score(best_validation):
            best_answer = reviewed_answer
            best_validation = reviewed_validation
            review_applied = changed

    return GaiaAnswer(
        task_id=task.task_id,
        submitted_answer=best_answer,
        question=task.question,
        file_path=file_path,
        validation=best_validation,
        attempts=max(best_attempt, 1),
        review_applied=review_applied,
        raw_answer=best_raw_answer,
        validation_history=validation_history,
    )


def build_gaia_submission(username: str, agent_code: str, answers: list[GaiaAnswer]) -> dict[str, Any]:
    return {
        "username": username.strip(),
        "agent_code": agent_code.strip(),
        "answers": [answer.to_submission_item() for answer in answers],
    }


def submit_gaia_answers(
    username: str,
    agent_code: str,
    answers: list[GaiaAnswer],
    api_base_url: str = GAIA_API_BASE_URL,
    timeout: int = 120,
) -> dict[str, Any]:
    """Envia respostas para `/submit` no formato esperado pelo avaliador."""
    payload = build_gaia_submission(username, agent_code, answers)
    validation = validate_gaia_submission(payload)
    if not validation.valid:
        raise ValueError("Submissão GAIA inválida: " + "; ".join(validation.errors))

    response = _request_json(_join_url(api_base_url, "/submit"), method="POST", payload=payload, timeout=timeout)
    return response if isinstance(response, dict) else {"response": response}


def _gaia_report_markdown(
    answers: list[GaiaAnswer],
    submission_validation: Any,
    submit_result: dict[str, Any] | None = None,
) -> str:
    lines = [
        "# Execução GAIA",
        "",
        f"## Resumo",
        f"- Tarefas respondidas: {len(answers)}",
        f"- Submissão local: {'válida' if submission_validation.valid else 'inválida'}",
        f"- Nota estática da submissão: {submission_validation.score}/10",
        "",
    ]

    if submission_validation.errors:
        lines.append("## Erros de validação")
        lines.extend(f"- {error}" for error in submission_validation.errors)
        lines.append("")

    if submission_validation.warnings:
        lines.append("## Alertas de validação")
        lines.extend(f"- {warning}" for warning in submission_validation.warnings)
        lines.append("")

    lines.append("## Respostas")
    lines.append("| Task ID | Resposta | Validação | Tentativas | Revisão |")
    lines.append("|---|---|---|---:|---|")
    for answer in answers:
        status = "válida" if answer.validation and answer.validation.valid else "inválida"
        safe_answer = answer.submitted_answer.replace("|", "\\|").replace("\n", " ")
        review_status = "sim" if answer.review_applied else "não"
        lines.append(f"| `{answer.task_id}` | {safe_answer} | {status} | {answer.attempts} | {review_status} |")

    if submit_result is not None:
        lines.extend([
            "",
            "## Resultado do avaliador remoto",
            "```json",
            json.dumps(submit_result, ensure_ascii=False, indent=2),
            "```",
        ])

    return "\n".join(lines) + "\n"


def run_gaia_benchmark(
    username: str = "",
    agent_code: str = "",
    max_tasks: int | None = None,
    submit: bool = False,
    api_base_url: str = GAIA_API_BASE_URL,
    save_outputs: bool = True,
) -> tuple[str, list[str] | None]:
    """Busca tarefas, resolve com o agente, valida, salva e opcionalmente submete."""
    questions = fetch_gaia_questions(api_base_url=api_base_url)
    if max_tasks and max_tasks > 0:
        questions = questions[:max_tasks]

    if not questions:
        return "# Execução GAIA\n\nNenhuma tarefa foi retornada pelo endpoint `/questions`.\n", None

    answers: list[GaiaAnswer] = []
    agent = get_gaia_agent()
    files_dir = GAIA_RUNS_DIR / "files"

    for task in questions:
        file_path = download_gaia_file(task, api_base_url=api_base_url, target_dir=files_dir) if task.file_name else None
        answers.append(answer_gaia_task(task, file_path=file_path, agent=agent))

    payload = build_gaia_submission(username, agent_code, answers)
    submission_validation = validate_gaia_submission(payload, require_identity=submit)

    submit_result = None
    if submit:
        if not submission_validation.valid:
            raise ValueError("Submissão GAIA inválida: " + "; ".join(submission_validation.errors))
        submit_result = submit_gaia_answers(username, agent_code, answers, api_base_url=api_base_url)

    report = _gaia_report_markdown(answers, submission_validation, submit_result=submit_result)
    file_paths = save_gaia_run(payload, report, submit_result) if save_outputs else None

    return report, file_paths
 