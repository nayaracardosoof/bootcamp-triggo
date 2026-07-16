from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StaticGradeResult:
    """Resultado de uma validação objetiva feita por código, não por LLM."""

    valid: bool
    score: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self, title: str = "Validação estática") -> str:
        status = "válido" if self.valid else "inválido"
        lines = [f"## {title}", f"- Status: {status}", f"- Nota estática: {self.score}/10"]

        if self.errors:
            lines.append("- Erros:")
            lines.extend(f"  - {error}" for error in self.errors)
        else:
            lines.append("- Erros: nenhum")

        if self.warnings:
            lines.append("- Alertas:")
            lines.extend(f"  - {warning}" for warning in self.warnings)
        else:
            lines.append("- Alertas: nenhum")

        return "\n".join(lines)


REQUIRED_SKILL_FRONTMATTER_FIELDS = ("name", "description", "version", "language")

REQUIRED_SKILL_SECTIONS = (
    "Objetivo",
    "Quando usar",
    "Entradas esperadas",
    "Saída esperada",
    "Pré-requisitos",
    "Passo a passo operacional",
    "Boas práticas",
    "Erros comuns",
    "Exemplo de uso",
    "Critérios de sucesso",
    "Referências consultadas",
)

RECOMMENDED_REPORT_SECTIONS = (
    "Resumo executivo",
    "Principais achados",
    "Recomendação prática",
)

PLACEHOLDER_PATTERNS = (
    r"\.\.\.",
    r"\[insira[^\]]*\]",
    r"\{\{[^}]+\}\}",
    r"TODO",
)

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_SIMPLE_YAML_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")


def strip_markdown_fences(content: str) -> str:
    """Remove cercas externas que o modelo às vezes adiciona em volta do artefato."""
    text = (content or "").strip()
    match = re.fullmatch(r"```(?:markdown|md)?\s*\n(?P<body>.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group("body").strip()
    return text


def extract_frontmatter(content: str) -> tuple[dict[str, str], str, list[str]]:
    """Extrai frontmatter YAML simples no formato `chave: valor`.

    Frontmatter é o bloco de metadados no começo do Markdown, entre duas linhas
    `---`. Exemplo:

    ---
    name: code-review
    description: Skill para revisar código.
    version: 1.0.0
    language: pt-BR
    ---
    """
    errors: list[str] = []
    text = strip_markdown_fences(content)
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text, ["Frontmatter YAML ausente ou não está no início do arquivo."]

    raw_frontmatter = match.group("body")
    data: dict[str, str] = {}

    for line_number, raw_line in enumerate(raw_frontmatter.splitlines(), start=2):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parsed = _SIMPLE_YAML_LINE_RE.match(line)
        if not parsed:
            errors.append(f"Linha inválida no frontmatter ({line_number}): {raw_line}")
            continue

        key, value = parsed.group(1), parsed.group(2).strip()
        if not value:
            errors.append(f"Campo '{key}' está vazio no frontmatter.")
            continue

        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        data[key] = value

    body = text[match.end() :].lstrip()
    return data, body, errors


def _headings(content: str) -> list[str]:
    return [match.group(2).strip().rstrip("#").strip() for match in _HEADING_RE.finditer(content or "")]


def _has_heading(content: str, expected: str) -> bool:
    expected_normalized = expected.casefold()
    return any(heading.casefold() == expected_normalized for heading in _headings(content))


def _has_skill_title(content: str) -> bool:
    return any(heading.casefold().startswith("skill:") for heading in _headings(content))


def _has_unclosed_code_fence(content: str) -> bool:
    return len(re.findall(r"^```", content or "", flags=re.MULTILINE)) % 2 == 1


def _find_placeholder_warnings(content: str) -> list[str]:
    warnings: list[str] = []
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, content or "", flags=re.IGNORECASE):
            warnings.append(f"Possível placeholder encontrado pelo padrão: {pattern}")
    return warnings


def _find_bad_links(content: str) -> list[str]:
    warnings: list[str] = []
    for link in _LINK_RE.findall(content or ""):
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        if link.strip() in {"", "url", "link"} or "exemplo" in link.casefold():
            warnings.append(f"Link possivelmente inválido ou placeholder: {link}")
    return warnings


def _score_from_issues(errors: list[str], warnings: list[str]) -> int:
    return max(0, 10 - (len(errors) * 2) - len(warnings))


def validate_skill_markdown(content: str) -> StaticGradeResult:
    """Valida uma skill em Markdown com frontmatter YAML obrigatório."""
    errors: list[str] = []
    warnings: list[str] = []
    text = strip_markdown_fences(content)

    if not text:
        return StaticGradeResult(False, 0, ["Skill vazia."], [], {})

    frontmatter, body, frontmatter_errors = extract_frontmatter(text)
    errors.extend(frontmatter_errors)

    for field_name in REQUIRED_SKILL_FRONTMATTER_FIELDS:
        if not frontmatter.get(field_name):
            errors.append(f"Campo obrigatório ausente no frontmatter: {field_name}")

    language = frontmatter.get("language")
    if language and language != "pt-BR":
        warnings.append("Campo 'language' deveria ser 'pt-BR'.")

    version = frontmatter.get("version")
    if version and not re.fullmatch(r"\d+\.\d+\.\d+", version):
        warnings.append("Campo 'version' deveria seguir semver, exemplo: 1.0.0.")

    name = frontmatter.get("name")
    if name and not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,68}[a-z0-9]", name):
        warnings.append("Campo 'name' deveria usar slug curto em minúsculas, exemplo: code-review.")

    if not _has_skill_title(body):
        errors.append("Título principal '# Skill: ...' ausente.")

    for section in REQUIRED_SKILL_SECTIONS:
        if not _has_heading(body, section):
            errors.append(f"Seção obrigatória ausente: {section}")

    if _has_unclosed_code_fence(body):
        errors.append("Bloco de código Markdown não fechado.")

    if re.search(r"```json|\{\s*\"schema_version\"|\{\s*\"type\"\s*:\s*\"skill\"", body, flags=re.IGNORECASE):
        errors.append("A skill parece conter JSON/manifest dentro do Markdown; o manifest deve ser arquivo separado.")

    if "# Avaliação" in body or "## Nota final" in body:
        errors.append("A skill parece conter avaliação; a avaliação deve ser arquivo separado.")

    warnings.extend(_find_placeholder_warnings(body))
    warnings.extend(_find_bad_links(body))

    return StaticGradeResult(
        valid=not errors,
        score=_score_from_issues(errors, warnings),
        errors=errors,
        warnings=warnings,
        metadata={"frontmatter": frontmatter, "sections_found": _headings(body)},
    )


def validate_report_markdown(content: str, require_sources: bool = False) -> StaticGradeResult:
    """Valida se um relatório Markdown é renderizável e tem estrutura humana mínima."""
    errors: list[str] = []
    warnings: list[str] = []
    text = strip_markdown_fences(content)

    if not text:
        return StaticGradeResult(False, 0, ["Relatório vazio."], [], {})

    headings = _headings(text)
    if not headings:
        errors.append("Relatório não possui títulos Markdown.")
    elif not re.search(r"^#\s+", text, flags=re.MULTILINE):
        errors.append("Relatório não possui título principal de nível 1 ('# ...').")

    for section in RECOMMENDED_REPORT_SECTIONS:
        if not _has_heading(text, section):
            warnings.append(f"Seção recomendada ausente: {section}")

    if require_sources and not _has_heading(text, "Fontes consultadas"):
        errors.append("Fontes foram solicitadas, mas a seção 'Fontes consultadas' está ausente.")

    if _has_unclosed_code_fence(text):
        errors.append("Bloco de código Markdown não fechado.")

    warnings.extend(_find_placeholder_warnings(text))
    warnings.extend(_find_bad_links(text))

    return StaticGradeResult(
        valid=not errors,
        score=_score_from_issues(errors, warnings),
        errors=errors,
        warnings=warnings,
        metadata={"sections_found": headings},
    )


def validate_skill_manifest(manifest_path: str | Path, markdown_path: str | Path | None = None) -> StaticGradeResult:
    """Valida o JSON manifest de carregamento de uma skill exportada."""
    errors: list[str] = []
    warnings: list[str] = []
    path = Path(manifest_path)

    if not path.exists():
        return StaticGradeResult(False, 0, [f"Manifest não encontrado: {path}"], [], {})

    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return StaticGradeResult(False, 0, [f"Manifest JSON inválido: {exc}"], [], {})

    required_fields = {
        "schema_version": str,
        "type": str,
        "id": str,
        "name": str,
        "description": str,
        "language": str,
        "content_file": str,
        "content_format": str,
        "created_at": str,
    }

    for field_name, field_type in required_fields.items():
        value = manifest.get(field_name)
        if value is None:
            errors.append(f"Campo obrigatório ausente no manifest: {field_name}")
        elif not isinstance(value, field_type):
            errors.append(f"Campo '{field_name}' deveria ser {field_type.__name__}.")
        elif isinstance(value, str) and not value.strip():
            errors.append(f"Campo '{field_name}' está vazio no manifest.")

    if manifest.get("type") != "skill":
        errors.append("Campo 'type' do manifest deve ser 'skill'.")
    if manifest.get("content_format") != "markdown":
        errors.append("Campo 'content_format' do manifest deve ser 'markdown'.")
    if manifest.get("language") != "pt-BR":
        warnings.append("Campo 'language' do manifest deveria ser 'pt-BR'.")

    content_file = manifest.get("content_file")
    expected_markdown = Path(markdown_path) if markdown_path else path.with_name(str(content_file))
    if content_file and not expected_markdown.exists():
        errors.append(f"Arquivo Markdown apontado pelo manifest não existe: {content_file}")
    elif content_file and Path(content_file).name != expected_markdown.name:
        errors.append("Campo 'content_file' não corresponde ao arquivo Markdown informado.")

    return StaticGradeResult(
        valid=not errors,
        score=_score_from_issues(errors, warnings),
        errors=errors,
        warnings=warnings,
        metadata={"manifest": manifest},
    )


_GAIA_BAD_PREFIXES = (
    "a resposta é",
    "a resposta final é",
    "resposta:",
    "resposta final:",
    "final answer:",
)


def validate_gaia_answer(answer: str) -> StaticGradeResult:
    """Valida objetivamente se uma resposta GAIA está limpa para submissão."""
    errors: list[str] = []
    warnings: list[str] = []
    text = (answer or "").strip()

    if not text:
        errors.append("Resposta vazia.")
    if "```" in text:
        errors.append("Resposta contém bloco Markdown; envie somente o valor final.")
    if re.search(r"^#{1,6}\s+", text, flags=re.MULTILINE):
        errors.append("Resposta contém título Markdown; envie somente o valor final.")
    if len(text) > 300:
        warnings.append("Resposta longa demais para GAIA; confirme se a tarefa não pedia apenas um valor curto.")
    if len([line for line in text.splitlines() if line.strip()]) > 3:
        warnings.append("Resposta contém muitas linhas; GAIA normalmente espera resposta curta.")

    lowered = text.casefold()
    if any(lowered.startswith(prefix) for prefix in _GAIA_BAD_PREFIXES):
        warnings.append("Resposta contém prefixo conversacional; prefira somente o valor final.")
    if re.search(r"\b(não sei|nao sei|não consegui|nao consegui|não posso determinar)\b", lowered):
        warnings.append("Resposta indica incerteza/incapacidade; verifique antes de submeter.")
    if text.lstrip().startswith(("{", "[")):
        warnings.append("Resposta parece JSON; GAIA geralmente espera uma string curta no campo submitted_answer.")

    return StaticGradeResult(
        valid=not errors,
        score=_score_from_issues(errors, warnings),
        errors=errors,
        warnings=warnings,
        metadata={"answer_length": len(text)},
    )


def validate_gaia_submission(payload: dict[str, Any], require_identity: bool = True) -> StaticGradeResult:
    """Valida o payload local antes de enviar para o avaliador GAIA."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return StaticGradeResult(False, 0, ["Payload de submissão deve ser um objeto JSON."], [], {})

    username = str(payload.get("username") or "").strip()
    agent_code = str(payload.get("agent_code") or "").strip()
    answers = payload.get("answers")

    if require_identity and not username:
        errors.append("Campo 'username' é obrigatório para submissão remota.")
    elif not username:
        warnings.append("Campo 'username' está vazio; preencha antes de submeter ao avaliador remoto.")

    if require_identity and not agent_code:
        errors.append("Campo 'agent_code' é obrigatório para submissão remota.")
    elif not agent_code:
        warnings.append("Campo 'agent_code' está vazio; preencha antes de submeter ao avaliador remoto.")

    if not isinstance(answers, list):
        errors.append("Campo 'answers' deve ser uma lista.")
        answers = []
    elif not answers:
        errors.append("Campo 'answers' está vazio.")

    seen_task_ids: set[str] = set()
    for index, item in enumerate(answers):
        if not isinstance(item, dict):
            errors.append(f"Resposta #{index + 1} deve ser um objeto.")
            continue

        task_id = str(item.get("task_id") or "").strip()
        submitted_answer = str(item.get("submitted_answer") or "").strip()

        if not task_id:
            errors.append(f"Resposta #{index + 1} sem task_id.")
        elif task_id in seen_task_ids:
            errors.append(f"task_id duplicado: {task_id}")
        else:
            seen_task_ids.add(task_id)

        answer_grade = validate_gaia_answer(submitted_answer)
        for error in answer_grade.errors:
            errors.append(f"Resposta {task_id or index + 1}: {error}")
        for warning in answer_grade.warnings:
            warnings.append(f"Resposta {task_id or index + 1}: {warning}")

    return StaticGradeResult(
        valid=not errors,
        score=_score_from_issues(errors, warnings),
        errors=errors,
        warnings=warnings,
        metadata={"answers_count": len(answers), "task_ids": sorted(seen_task_ids)},
    )
 