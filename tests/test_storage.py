import json
from pathlib import Path

from research_report_agent.storage import save_evaluation, save_markdown, save_skill, slugify


def test_slugify_generates_safe_filename_part():
    assert slugify("Crie uma skill pra Code Review!!!") == "crie-uma-skill-pra-code-review"
    assert slugify("   ") == "pesquisa"


def test_save_markdown_creates_file(tmp_path: Path):
    file_path = save_markdown(
        question="Teste de relatório",
        content="# Conteúdo de teste\n",
        directory=tmp_path,
        prefix="relatorio",
    )

    saved_file = Path(file_path)

    assert saved_file.exists()
    assert saved_file.suffix == ".md"
    assert "relatorio" in saved_file.name
    assert saved_file.read_text(encoding="utf-8") == "# Conteúdo de teste\n"


def test_save_skill_creates_markdown_and_manifest(monkeypatch, tmp_path: Path):
    import research_report_agent.storage as storage

    monkeypatch.setattr(storage, "GENERATED_SKILLS_DIR", tmp_path)

    file_paths = save_skill(
        question="Crie uma skill pra Code Review",
        content="# Skill: Code Review\n",
    )

    assert len(file_paths) == 2

    markdown_path = Path(file_paths[0])
    manifest_path = Path(file_paths[1])

    assert markdown_path.exists()
    assert markdown_path.suffix == ".md"
    assert "skill" in markdown_path.name
    assert markdown_path.read_text(encoding="utf-8") == "# Skill: Code Review\n"

    assert manifest_path.exists()
    assert manifest_path.suffix == ".json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["type"] == "skill"
    assert manifest["content_file"] == markdown_path.name
    assert manifest["content_format"] == "markdown"
    assert manifest["language"] == "pt-BR"


def test_save_evaluation_uses_evaluation_prefix(monkeypatch, tmp_path: Path):
    import research_report_agent.storage as storage

    monkeypatch.setattr(storage, "EVALUATIONS_DIR", tmp_path)

    file_path = save_evaluation(
        question="Crie uma skill pra Code Review",
        content="# Avaliação\n",
    )

    saved_file = Path(file_path)

    assert saved_file.exists()
    assert "avaliacao" in saved_file.name
    assert saved_file.read_text(encoding="utf-8") == "# Avaliação\n"
 