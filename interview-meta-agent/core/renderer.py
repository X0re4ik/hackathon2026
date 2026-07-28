from __future__ import annotations

from datetime import datetime
from typing import Any

import yaml

from core.schema import InterviewMeta, ValidationError, ValidationResult


def validate_meta(data: dict) -> ValidationResult:
    errors = []
    if "meta_id" not in data:
        errors.append(ValidationError(field="meta_id", message="meta_id is required"))
    if "source" not in data:
        errors.append(ValidationError(field="source", message="source block is required"))
    elif "reference" not in data["source"] or not data["source"]["reference"]:
        errors.append(ValidationError(field="source.reference", message="source.reference is required"))

    pains = data.get("pains", [])
    if not pains:
        errors.append(ValidationError(field="pains", message="at least one pain is required"))
    else:
        for i, p in enumerate(pains):
            if not p.get("title"):
                errors.append(ValidationError(field=f"pains[{i}].title", message="pain title is required"))
            if not p.get("quote"):
                errors.append(ValidationError(field=f"pains[{i}].quote", message="pain quote is required"))

    if errors:
        return ValidationResult(valid=False, errors=errors)

    try:
        InterviewMeta(**data)
        return ValidationResult(valid=True)
    except Exception as e:
        return ValidationResult(valid=False, errors=[ValidationError(field="schema", message=str(e))])


def meta_to_dict(meta: InterviewMeta) -> dict:
    d = meta.model_dump(mode="json", exclude_none=True)
    return _clean_empty(d)


def _clean_empty(d: Any) -> Any:
    if isinstance(d, dict):
        return {k: _clean_empty(v) for k, v in d.items() if v not in (None, [], {}, "")}
    if isinstance(d, list):
        cleaned = [_clean_empty(i) for i in d if i not in (None, [], {}, "")]
        return cleaned if cleaned else None
    return d


def render_markdown(meta: InterviewMeta) -> str:
    d = meta_to_dict(meta)
    processed_at = d.pop("processed_at", None) or datetime.now().isoformat()
    agent_version = d.pop("agent_version", None) or "0.1.0"
    d["processed_at"] = processed_at
    d["agent_version"] = agent_version

    header = "---\n"
    header += yaml.dump(d, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)
    if header.endswith("\n\n"):
        header = header.rstrip("\n") + "\n"
    header += "---\n\n"

    title = f"# {meta.meta_id}"
    if meta.respondent and meta.respondent.role:
        title += f" — {meta.respondent.role}"
    if meta.respondent and meta.respondent.customer_status:
        title += f", {meta.respondent.customer_status}"
    if meta.source and meta.source.origin:
        title += f"\n*Источник: {meta.source.origin} ({meta.source.reference})*"

    body = title + "\n\n"

    body += _render_summary(meta)
    body += _render_pain_table(meta)
    body += _render_agent_commentary(meta)

    return header + body


def _render_summary(meta: InterviewMeta) -> str:
    lines = ["## Резюме\n"]
    if meta.interview_commentary and meta.interview_commentary.who_and_expectations:
        lines.append(meta.interview_commentary.who_and_expectations + "\n")
    if meta.segment:
        lines.append(f"**Сегмент:** {meta.segment.type}")
        if meta.segment.subtype:
            lines.append(f" ({meta.segment.subtype})")
        lines.append("\n")
    if meta.respondent and meta.respondent.quote:
        lines.append(f"\n> {meta.respondent.quote}\n")
    lines.append("\n")
    return "".join(lines)


def _render_pain_table(meta: InterviewMeta) -> str:
    if not meta.pains:
        return ""
    lines = ["## Карта болей\n\n"]
    lines.append("| # | Боль | Природа | Trust | Сигналы | Эмоция |\n")
    lines.append("|---|------|---------|:-----:|---------|--------|\n")
    for p in meta.pains:
        n = p.commentary.pain_nature if p.commentary else ""
        tb = "✔" if p.trust_breach else ""
        signals = []
        if p.spontaneous:
            signals.append("спонтанно")
        if p.past_behavior:
            signals.append("past_behavior")
        if p.workaround:
            signals.append("workaround")
        if p.frequency and p.frequency != "unknown":
            signals.append(p.frequency)
        sig_str = ", ".join(signals) if signals else ""
        emo = ""
        if p.emotion:
            ev = f"{p.emotion.valence}/{p.emotion.intensity}" if p.emotion.valence is not None and p.emotion.intensity is not None else ""
            mk = ", ".join(p.emotion.markers) if p.emotion.markers else ""
            emo = f"{ev} {mk}".strip()
        p_id = p.id.split("-")[-1]
        lines.append(f"| {p_id} | {p.title} | {n} | {tb} | {sig_str} | {emo} |\n")
    lines.append("\n")
    return "".join(lines)


def _render_agent_commentary(meta: InterviewMeta) -> str:
    if not meta.interview_commentary:
        return ""
    ic = meta.interview_commentary
    lines = ["## Комментарий агента\n\n"]
    if ic.who_and_expectations:
        lines.append(f"**Кто пришёл и с чем:** {ic.who_and_expectations}\n\n")
    if ic.expectations_vs_experience:
        lines.append(f"**Ожидания vs реальность:** {ic.expectations_vs_experience}\n\n")
    if ic.audience_fit_signals:
        lines.append(f"**Сигналы о ЦА:** {ic.audience_fit_signals}\n\n")
    if ic.evidence_quality:
        lines.append(f"**Качество свидетельств:** {ic.evidence_quality}\n\n")
    if ic.churn_driver_hypotheses:
        lines.append("**Гипотезы причин ухода:**\n")
        for h in ic.churn_driver_hypotheses:
            lines.append(f"- {h}\n")
        lines.append("\n")
    lines.append("\n---\n\n")
    lines.append(
        "> **Оценка важности и приоритета болей — вне компетенции этого агента.**\n"
        "> Он не знает продукт, его ЦА и стратегию. Здесь только факты, сигналы и гипотезы.\n"
    )
    return "".join(lines)
