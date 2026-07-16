import json
from pathlib import Path

from research_report_agent.gaia import (
    GaiaAnswer,
    GaiaQuestion,
    answer_gaia_task,
    build_gaia_submission,
    fetch_gaia_questions,
    normalize_gaia_answer,
    review_gaia_answer,
)
from research_report_agent.prompts import build_gaia_answer_prompt
from research_report_agent.static_grader import validate_gaia_answer, validate_gaia_submission
from research_report_agent.storage import save_gaia_run


class FakeAgent:
    def __init__(self, response: str):
        self.response = response
        self.prompts = []

    def run(self, prompt: str):
        self.prompts.append(prompt)
        return self.response


def test_build_gaia_answer_prompt_requires_short_final_answer():
    prompt = build_gaia_answer_prompt(
        question="Who wrote Hamlet?",
        file_path="C:/tmp/file.txt",
        task_id="task-1",
    )

    assert "benchmark GAIA" in prompt
    assert "task-1" in prompt
    assert "Who wrote Hamlet?" in prompt
    assert "C:/tmp/file.txt" in prompt
    assert "Responda somente com a resposta final curta" in prompt
    assert "Não inclua Markdown" in prompt


def test_normalize_gaia_answer_removes_prefixes_and_fences():
    assert normalize_gaia_answer("FINAL ANSWER: Paris") == "Paris"
    assert normalize_gaia_answer('```text\nResposta final: 42\n```') == "42"


def test_validate_gaia_answer_rejects_empty_and_markdown():
    assert validate_gaia_answer("Paris").valid is True

    empty = validate_gaia_answer("")
    assert empty.valid is False
    assert any("vazia" in error for error in empty.errors)

    markdown = validate_gaia_answer("# Resposta\nParis")
    assert markdown.valid is False
    assert any("Markdown" in error for error in markdown.errors)


def test_build_and_validate_gaia_submission():
    answers = [GaiaAnswer(task_id="abc", submitted_answer="Paris")]
    payload = build_gaia_submission("usuario", "https://hf.co/spaces/u/a", answers)

    assert payload == {
        "username": "usuario",
        "agent_code": "https://hf.co/spaces/u/a",
        "answers": [{"task_id": "abc", "submitted_answer": "Paris"}],
    }
    assert validate_gaia_submission(payload).valid is True


def test_validate_gaia_submission_rejects_duplicate_task_id():
    payload = {
        "username": "usuario",
        "agent_code": "agent",
        "answers": [
            {"task_id": "abc", "submitted_answer": "Paris"},
            {"task_id": "abc", "submitted_answer": "Lyon"},
        ],
    }

    result = validate_gaia_submission(payload)

    assert result.valid is False
    assert any("duplicado" in error for error in result.errors)


def test_answer_gaia_task_uses_agent_and_normalizes():
    agent = FakeAgent("Resposta final: Marie Curie")
    task = GaiaQuestion(task_id="t1", question="Quem descobriu o polônio?")

    answer = answer_gaia_task(task, agent=agent, review=False)

    assert answer.task_id == "t1"
    assert answer.submitted_answer == "Marie Curie"
    assert answer.validation.valid is True
    assert "Quem descobriu" in agent.prompts[0]


def test_fetch_gaia_questions_accepts_enveloped_response(monkeypatch):
    import research_report_agent.gaia as gaia

    monkeypatch.setattr(
        gaia,
        "_request_json",
        lambda url, timeout=60, **kwargs: {
            "questions": [
                {"task_id": "1", "question": "Pergunta 1", "file_name": "a.txt"},
                {"task_id": "2", "question": "Pergunta 2"},
            ]
        },
    )

    questions = fetch_gaia_questions("https://example.test")

    assert len(questions) == 2
    assert questions[0].task_id == "1"
    assert questions[0].file_name == "a.txt"


def test_save_gaia_run_creates_answers_report_and_result(monkeypatch, tmp_path: Path):
    import research_report_agent.storage as storage

    monkeypatch.setattr(storage, "GAIA_RUNS_DIR", tmp_path)
    payload = {
        "username": "usuario",
        "agent_code": "agent",
        "answers": [{"task_id": "abc", "submitted_answer": "Paris"}],
    }

    paths = save_gaia_run(payload, "# Execução GAIA\n", {"score": 1})

    assert len(paths) == 3
    assert all(Path(path).exists() for path in paths)
    assert json.loads(Path(paths[0]).read_text(encoding="utf-8"))["answers"][0]["submitted_answer"] == "Paris"
    assert Path(paths[1]).read_text(encoding="utf-8") == "# Execução GAIA\n"



class SequenceAgent:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def run(self, prompt: str):
        self.prompts.append(prompt)
        if self.responses:
            return self.responses.pop(0)
        return "fallback"


def test_answer_gaia_task_retries_when_first_answer_is_invalid():
    agent = SequenceAgent(["# Resposta\nParis", "Paris"])
    reviewer = FakeAgent("Paris")
    task = GaiaQuestion(task_id="t-retry", question="Capital da França?")

    answer = answer_gaia_task(task, agent=agent, reviewer_agent=reviewer, max_attempts=2)

    assert answer.submitted_answer == "Paris"
    assert answer.attempts == 2
    assert answer.validation.valid is True
    assert len(agent.prompts) == 2
    assert "Resposta anterior" in agent.prompts[1]


def test_review_gaia_answer_cleans_format_without_changing_fact():
    task = GaiaQuestion(task_id="t-review", question="Quem escreveu Hamlet?")
    reviewer = FakeAgent("William Shakespeare")

    answer, validation, changed = review_gaia_answer(
        task,
        "A resposta final é: William Shakespeare",
        reviewer_agent=reviewer,
    )

    assert answer == "William Shakespeare"
    assert validation.valid is True
    assert changed is False
    assert "Resposta candidata" in reviewer.prompts[0]


def test_answer_gaia_task_can_apply_reviewer_cleanup():
    agent = FakeAgent("Paris")
    reviewer = FakeAgent("Paris")
    task = GaiaQuestion(task_id="t-review-flow", question="Capital da França?")

    answer = answer_gaia_task(task, agent=agent, reviewer_agent=reviewer, max_attempts=1)

    assert answer.submitted_answer == "Paris"
    assert answer.review_applied is False
    assert answer.validation.valid is True
    assert answer.validation_history
 