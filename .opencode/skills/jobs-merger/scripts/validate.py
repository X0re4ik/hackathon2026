#!/usr/bin/env python3
"""
Валидатор свода jobs-merger. ОПЦИОНАЛЬНЫЙ инструмент.

Скилл jobs-merger работает без него: чек-лист финализации агент проходит сам.
Скрипт нужен, чтобы проверить результат объективно и быстро — без чтения свода
целиком человеком.

Проверяет то, что проверяемо машинно:
  - вхождения, ссылки, структуру;
  - доли фасетов A/* и B/* — пересчитывает из мет и сверяет с записанным;
  - флаги критичности — пересчитывает из мет и сверяет;
  - согласованность churn-driver с цитатой гипотезы ухода.

Смысловые решения не оценивает: слияние тем и доли C/* — суждение агента.

Использование:
    python3 jobs-merger/scripts/validate.py [--meta output/meta] [--summary output/OUTPUT.md]

Код возврата: 0 — ошибок нет, 1 — есть ошибки.
Требует pyyaml.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("нужен pyyaml: pip install pyyaml")

# допуск на округление доли до целых процентов
PCT_TOL = 2
MOTIVE_LIMIT = 8
FLAG_WEIGHTS = {
    "churn-driver": 3,
    "trust-breach": 1,
    "hi-freq": 1,
    "no-workaround": 1,
    "multi-interview": 1,
    "multi-segment": 1,
}
DETERMINISTIC_FACETS = ("A/segment", "A/status", "B/nature", "B/freq")


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Разрез по строкам, состоящим РОВНО из '---'.

    Наивный text.split('---') ломается, если внутри frontmatter есть комментарий
    вида '# --- группа A ---'. Поэтому режем построчно.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("нет YAML frontmatter")
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return yaml.safe_load("".join(lines[1:i])) or {}, "".join(lines[i + 1 :])
    raise ValueError("frontmatter не закрыт строкой '---'")


def load_metas(folder: str) -> dict[str, dict]:
    metas = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.md"))):
        fm, _ = split_frontmatter(open(path, encoding="utf-8").read())
        mid = fm.get("meta_id") or os.path.splitext(os.path.basename(path))[0]
        metas[mid] = fm
    return metas


def pain_index(meta: dict) -> dict[str, dict]:
    """Локальный id боли ('p1') → боль. В мете id может быть полным (META-...-p1)."""
    return {p["id"].split("-")[-1]: p for p in (meta.get("pains") or [])}


def parse_themes_table(body: str) -> list[dict]:
    """Строки таблицы «Темы» — до первого заголовка секции темы."""
    cut = re.search(r"^## T-", body, re.M)
    head = body[: cut.start()] if cut else body
    rows = []
    for line in head.splitlines():
        m = re.match(r"^\|\s*(T-\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|", line)
        if m:
            rows.append(
                {
                    "id": m.group(1),
                    "title": m.group(2).strip(),
                    "tags": [t.strip() for t in m.group(3).split(",") if t.strip()],
                    "metas": [t.strip() for t in m.group(4).split(",") if t.strip()],
                }
            )
    return rows


def parse_shares(chunk: str) -> dict[str, dict[str, int]]:
    """Строка **Доли:** → {фасет: {значение тега: процент}}.

    Формат: `A/segment: business 67%, individual 33% | B/freq: monthly 100%`
    Значения — короткие (без префикса), как их пишет агент.
    """
    m = re.search(r"\*\*Доли:\*\*(.+?)(?=\n\s*\n|\n\*\*)", chunk, re.S)
    if not m:
        return {}
    raw = " ".join(m.group(1).split())
    out: dict[str, dict[str, int]] = {}
    for part in raw.split("|"):
        part = part.strip()
        if not part:
            continue
        fm_ = re.match(r"^([A-DС/a-zа-яё]+/[^:]+):\s*(.+)$", part)
        if not fm_:
            continue
        facet, rest = fm_.group(1).strip(), fm_.group(2)
        vals: dict[str, int] = {}
        for item in rest.split(","):
            im = re.match(r"^\s*(.+?)\s+(\d+)\s*%\s*$", item)
            if im:
                vals[im.group(1).strip()] = int(im.group(2))
        if vals:
            out[facet] = vals
    return out


def parse_sections(body: str) -> dict[str, dict]:
    """Секции тем: ## T-NN — Название, с Job, Теги, Доли, Сигналы, Участники."""
    sections = {}
    parts = re.split(r"^## (T-\d+)\s*[—-]\s*(.*)$", body, flags=re.M)
    for i in range(1, len(parts), 3):
        tid, title, chunk = parts[i], parts[i + 1].strip(), parts[i + 2]
        chunk = re.split(r"^## ", chunk, flags=re.M)[0]

        job = re.search(r"\*\*Job:\*\*(.+?)(?=\n\s*\n|\*\*Теги)", chunk, re.S)
        tags = re.search(r"\*\*Теги:\*\*(.+?)(?=\n\s*\n|\*\*Доли|\*\*Сигналы|\*\*Участники)", chunk, re.S)
        signals = re.search(r"\*\*Сигналы:\*\*(.+?)(?=\n\s*\n|\n\*\*)", chunk, re.S)

        # участники и их боли: строка участника + опциональная вложенная строка «боли:»
        participants: list[tuple[str, str]] = []
        pains_by_part: list[tuple[str, set[str]]] = []
        for line in chunk.splitlines():
            pm = re.match(r"^-\s*(\S+)\s*\((\w+)\)\s*:", line)
            if pm:
                participants.append((pm.group(1), pm.group(2)))
                pains_by_part.append((pm.group(1), set()))
                continue
            bm = re.match(r"^\s+боли:\s*(.+)$", line)
            if bm and pains_by_part:
                pains_by_part[-1][1].update(re.findall(r"\bp\d+\b", bm.group(1)))

        churn = re.findall(
            r"\*\*Причина ухода:\*\*\s*(\S+)\s*\(([^)]*)\)\s*:\s*(.+?)(?=\n\s*\n|\n\*\*|\Z)",
            chunk,
            re.S,
        )

        sections[tid] = {
            "title": title,
            "job": " ".join(job.group(1).split()) if job else "",
            "tags": [t.strip() for t in tags.group(1).replace("\n", " ").split(",") if t.strip()]
            if tags
            else [],
            "shares": parse_shares(chunk),
            # «—» означает «флагов нет» — это законно, балл темы 0
            "signals": [
                s.strip()
                for s in signals.group(1).replace("\n", " ").split(",")
                if s.strip() and s.strip() not in ("—", "-", "–")
            ]
            if signals
            else [],
            "has_signals_line": bool(signals),
            "participants": participants,
            "pains_by_part": pains_by_part,
            "churn": [(c[0], c[1].strip(), " ".join(c[2].split())) for c in churn],
            "overflow": "overflow: true" in chunk,
        }
    return sections


def parse_orphans(body: str) -> list[tuple[str, str]]:
    m = re.search(r"^## Боли вне jobs\s*(.*?)(?=^## |\Z)", body, re.S | re.M)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and not cells[0].startswith("-") and cells[0] not in ("Боль", ""):
            pid = cells[0].split()[0]
            out.append((pid, cells[1]))
    return out


def linked_pains(sec: dict, metas: dict) -> list[dict]:
    """Боли темы, дедуплицированные по (meta_id, pain_id)."""
    seen: set[tuple[str, str]] = set()
    out = []
    for mid, pids in sec["pains_by_part"]:
        if mid not in metas:
            continue
        idx = pain_index(metas[mid])
        for pid in pids:
            if (mid, pid) in seen or pid not in idx:
                continue
            seen.add((mid, pid))
            out.append(idx[pid])
    return out


def pct(counter: dict[str, int]) -> dict[str, float]:
    total = sum(counter.values())
    return {k: v / total * 100 for k, v in counter.items()} if total else {}


def expected_shares(sec: dict, metas: dict) -> dict[str, dict[str, float]]:
    """Детерминированные фасеты: A/* по уникальным интервью, B/* по привязанным болям."""
    out: dict[str, dict[str, float]] = {}
    ivs = sorted({m for m, _ in sec["participants"] if m in metas})

    seg: dict[str, int] = {}
    sta: dict[str, int] = {}
    for mid in ivs:
        s = (metas[mid].get("segment") or {}).get("type")
        if s and s != "unknown":
            seg[s] = seg.get(s, 0) + 1
        st = (metas[mid].get("respondent") or {}).get("customer_status")
        if st and st != "unknown":
            sta[st] = sta.get(st, 0) + 1
    if seg:
        out["A/segment"] = pct(seg)
    if sta:
        out["A/status"] = pct(sta)

    nat: dict[str, int] = {}
    frq: dict[str, int] = {}
    for p in linked_pains(sec, metas):
        n = (p.get("commentary") or {}).get("pain_nature")
        if n and n != "unknown":
            nat[n] = nat.get(n, 0) + 1
        f = p.get("frequency")
        if f and f != "unknown":
            frq[f] = frq.get(f, 0) + 1
    if nat:
        out["B/nature"] = pct(nat)
    if frq:
        out["B/freq"] = pct(frq)
    return out


def expected_flags(sec: dict, metas: dict) -> set[str]:
    """Все флаги, кроме churn-driver: он требует суждения и проверяется через цитату."""
    flags: set[str] = set()
    pains = linked_pains(sec, metas)
    ivs = {m for m, _ in sec["participants"] if m in metas}

    if any(p.get("trust_breach") for p in pains):
        flags.add("trust-breach")
    if any(p.get("frequency") in ("daily", "weekly") for p in pains):
        flags.add("hi-freq")
    if pains and not any((p.get("workaround") or "").strip() for p in pains):
        flags.add("no-workaround")
    if len(ivs) >= 2:
        flags.add("multi-interview")
    if len({(metas[m].get("segment") or {}).get("type") for m in ivs} - {None, "unknown"}) >= 2:
        flags.add("multi-segment")
    return flags


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", default="output/meta")
    ap.add_argument("--summary", default="output/OUTPUT.md")
    ap.add_argument("--limit", type=int, default=30, help="лимит числа тем")
    args = ap.parse_args()

    metas = load_metas(args.meta)
    fm, body = split_frontmatter(open(args.summary, encoding="utf-8").read())

    sources = {s["meta_id"] for s in (fm.get("sources") or [])}
    tag_defs = {d["tag"]: d for d in (fm.get("tag_definitions") or [])}
    defined = set(tag_defs)
    themes = parse_themes_table(body)
    sections = parse_sections(body)
    orphans = parse_orphans(body)

    errors: list[str] = []
    warnings: list[str] = []

    # 1. все меты обработаны
    for mid in metas:
        if mid not in sources:
            warnings.append(f"мета {mid} ещё не обработана (нет в sources[])")
    for mid in sources - set(metas):
        errors.append(f"sources[] ссылается на {mid}, которого нет в {args.meta}")

    # 2. таблица тем и секции согласованы
    tbl_ids, sec_ids = {t["id"] for t in themes}, set(sections)
    for tid in tbl_ids - sec_ids:
        errors.append(f"{tid} есть в таблице «Темы», но секции нет")
    for tid in sec_ids - tbl_ids:
        errors.append(f"секция {tid} есть, но строки в таблице «Темы» нет")

    # 3. каждая тема непуста, участники валидны
    for tid, sec in sections.items():
        if not sec["job"]:
            errors.append(f"{tid}: нет канонической формулировки **Job:**")
        if not sec["participants"]:
            errors.append(f"{tid}: нет ни одного участника")
        for mid, jid in sec["participants"]:
            if mid not in metas:
                errors.append(f"{tid}: участник ссылается на неизвестную мету {mid}")
                continue
            jids = {j.get("id") for j in (metas[mid].get("jobs") or [])}
            if jid not in jids:
                errors.append(f"{tid}: у {mid} нет job с id={jid} (есть {sorted(jids)})")

    # 4. таблица тем: список мет совпадает с участниками секции
    for t in themes:
        sec = sections.get(t["id"])
        if not sec:
            continue
        from_sec = {m for m, _ in sec["participants"]}
        if set(t["metas"]) != from_sec:
            errors.append(
                f"{t['id']}: в таблице интервью {sorted(t['metas'])}, "
                f"а среди участников {sorted(from_sec)}"
            )
        stale = set(t["tags"]) - set(sec["tags"])
        if stale:
            errors.append(f"{t['id']}: теги {sorted(stale)} есть в таблице, но не в секции темы")

    # 5. все теги определены, у C есть kind, группы заполнены
    used: set[str] = set()
    for t in themes:
        used |= set(t["tags"])
    for sec in sections.values():
        used |= set(sec["tags"])
    for tag in sorted(used):
        if tag not in defined:
            errors.append(f"тег «{tag}» использован, но отсутствует в tag_definitions")
    seen: set[str] = set()
    for d in fm.get("tag_definitions") or []:
        tag = d.get("tag")
        if not str(d.get("definition", "")).strip():
            errors.append(f"тег «{tag}» без определения")
        if not d.get("group"):
            errors.append(f"тег «{tag}» без поля group")
        if d.get("group") == "C" and not d.get("kind"):
            errors.append(f"тег «{tag}» группы C без поля kind (домен|мотив)")
        want = next((f for p, f in (("segment:", "A/segment"), ("status:", "A/status"),
                                    ("nature:", "B/nature"), ("freq:", "B/freq"))
                     if str(tag).startswith(p)), None)
        if want and d.get("facet") != want:
            errors.append(f"тег «{tag}»: facet должен быть «{want}», а не «{d.get('facet')}»")
        if not want and d.get("facet"):
            errors.append(f"тег «{tag}»: facet «{d.get('facet')}» лишний — тег вне фасетных осей")
        if d.get("kind") and d.get("kind") not in ("домен", "мотив"):
            errors.append(f"тег «{tag}»: kind должен быть «домен» или «мотив», а не «{d.get('kind')}»")
        if tag in seen:
            errors.append(f"тег «{tag}» определён дважды")
        seen.add(tag)
    for tag in sorted(defined - used):
        warnings.append(f"тег «{tag}» определён, но нигде не используется — удалить на финализации")

    # 5a. лимит мотивов
    motives = [t for t, d in tag_defs.items() if d.get("kind") == "мотив" and t in used]
    if len(motives) > MOTIVE_LIMIT:
        errors.append(f"мотивов {len(motives)} > лимита {MOTIVE_LIMIT}: {sorted(motives)}")

    # 6. ни один job не потерян
    placed: set[tuple[str, str]] = set()
    for sec in sections.values():
        placed |= set(sec["participants"])
    for mid in sources & set(metas):
        for j in metas[mid].get("jobs") or []:
            if (mid, j["id"]) not in placed:
                errors.append(f"job {mid}/{j['id']} обработанной меты не попал ни в одну тему")
    for mid, jid in placed:
        if sum(1 for s in sections.values() if (mid, jid) in s["participants"]) > 1:
            errors.append(f"job {mid}/{jid} размещён более чем в одной теме")

    # 7. ни одна боль не потеряна (с привязкой к своей мете)
    linked_pairs: set[tuple[str, str]] = set()
    for sec in sections.values():
        for mid, pids in sec["pains_by_part"]:
            linked_pairs |= {(mid, pid) for pid in pids}
    orphan_pairs = {(mid, pid) for pid, mid in orphans}
    for mid in sources & set(metas):
        for pid in pain_index(metas[mid]):
            if (mid, pid) not in linked_pairs and (mid, pid) not in orphan_pairs:
                warnings.append(f"боль {mid}/{pid} не привязана к теме и не в «Боли вне jobs»")

    # 8. лимит тем
    if len(themes) > args.limit:
        over = [t["id"] for t in themes if sections.get(t["id"], {}).get("overflow")]
        if not over:
            errors.append(f"тем {len(themes)} > лимита {args.limit}, но ни одна не помечена overflow: true")

    # 9. структура: «## Темы» до первой секции темы
    i_t, m_sec = body.find("## Темы"), re.search(r"^## T-", body, re.M)
    if i_t < 0:
        errors.append("нет раздела «## Темы»")
    elif m_sec and i_t > m_sec.start():
        errors.append("«## Темы» идёт ПОСЛЕ секций тем — правило 1 скилла нарушено")

    # 10. заголовок совпадает с sources[]
    m_head = re.search(r"\*\*Интервью в своде:\*\*\s*(.+)", body)
    if m_head:
        listed = {x.strip() for x in m_head.group(1).split(",") if x.strip() and "нет" not in x}
        if listed != sources:
            errors.append(f"в заголовке {sorted(listed)}, в sources[] {sorted(sources)}")

    # 11. доли: наличие, сумма 100, совпадение с пересчётом из мет
    group_d = {t for t, d in tag_defs.items() if d.get("group") == "D"}
    scores: dict[str, int] = {}
    for tid, sec in sections.items():
        if not sec["shares"]:
            errors.append(f"{tid}: нет строки **Доли:**")
        for facet, vals in sec["shares"].items():
            total = sum(vals.values())
            if total != 100:
                errors.append(f"{tid}: фасет {facet} даёт {total}%, а не 100%")
            for v in vals:
                if v in group_d or f"evidence:{v}" in group_d or f"emotion:{v}" in group_d:
                    errors.append(f"{tid}: тег группы D «{v}» не может участвовать в долях")

        exp = expected_shares(sec, metas)
        for facet, evals in exp.items():
            got = sec["shares"].get(facet)
            if got is None:
                errors.append(f"{tid}: фасет {facet} должен быть (есть данные), но не записан")
                continue
            for val, epc in evals.items():
                gpc = got.get(val)
                if gpc is None:
                    errors.append(f"{tid}/{facet}: нет значения «{val}», ожидалось ~{epc:.0f}%")
                elif abs(gpc - epc) > PCT_TOL:
                    errors.append(
                        f"{tid}/{facet}: «{val}» записано {gpc}%, "
                        f"а по метам {epc:.0f}% (допуск {PCT_TOL})"
                    )
            for val in set(got) - set(evals):
                errors.append(f"{tid}/{facet}: значение «{val}» записано, но в метах его нет")
        for facet in set(sec["shares"]) - set(exp) - {"C/домен", "C/мотив"}:
            warnings.append(f"{tid}: неизвестный фасет «{facet}»")

    # 12. сигналы: пересчёт из мет + связь churn-driver с цитатой
    for tid, sec in sections.items():
        if not sec["has_signals_line"]:
            errors.append(f"{tid}: нет строки **Сигналы:** (нет флагов — пиши «—»)")
        got = set(sec["signals"])
        unknown = got - set(FLAG_WEIGHTS)
        for f in sorted(unknown):
            errors.append(f"{tid}: неизвестный флаг «{f}»")
        exp = expected_flags(sec, metas)
        for f in sorted(exp - got):
            errors.append(f"{tid}: флаг «{f}» должен стоять по данным мет, но не записан")
        for f in sorted((got & set(FLAG_WEIGHTS)) - exp - {"churn-driver"}):
            errors.append(f"{tid}: флаг «{f}» записан, но по данным мет не подтверждается")

        # churn-driver ⟺ есть строка «Причина ухода» с валидной ссылкой и цитатой
        has_flag = "churn-driver" in got
        if has_flag and not sec["churn"]:
            errors.append(f"{tid}: флаг churn-driver без строки **Причина ухода:** с цитатой")
        if sec["churn"] and not has_flag:
            errors.append(f"{tid}: есть **Причина ухода:**, но флаг churn-driver не выставлен")
        theme_ivs = {m for m, _ in sec["participants"]}
        for mid, status, quote in sec["churn"]:
            if mid not in metas:
                errors.append(f"{tid}: **Причина ухода:** ссылается на неизвестную мету {mid}")
                continue
            if mid not in theme_ivs:
                errors.append(f"{tid}: **Причина ухода:** от {mid}, который не участник темы")
            if len(quote.strip("«».,  ")) < 10:
                errors.append(f"{tid}: **Причина ухода:** от {mid} без содержательной цитаты")
            real = (metas[mid].get("respondent") or {}).get("customer_status")
            if status and real and status != real:
                errors.append(f"{tid}: **Причина ухода:** {mid} помечен «{status}», в мете «{real}»")
            if real not in ("churned", "churning"):
                errors.append(
                    f"{tid}: **Причина ухода:** от {mid} со статусом «{real}» — "
                    f"это риск, а не состоявшийся уход; флаг churn-driver не обоснован"
                )

        scores[tid] = sum(FLAG_WEIGHTS[f] for f in got if f in FLAG_WEIGHTS)

    # 13. разделы финализации заполнены (только если все меты обработаны)
    if set(metas) == sources:
        for head in ("## Критичность", "## Легенда групп тегов", "## Облако тегов", "## Наблюдения агента"):
            m = re.search(rf"^{re.escape(head)}\s*(.*?)(?=^## |\Z)", body, re.S | re.M)
            if not m:
                errors.append(f"нет раздела «{head}»")
            elif "Собирается на финализации" in m.group(1) or len(m.group(1).strip()) < 40:
                errors.append(f"раздел «{head}» не заполнен")
        for g in ("A", "B", "C", "D"):
            if not re.search(rf"^### Группа {g}\b", body, re.M):
                errors.append(f"в облаке тегов нет блока «### Группа {g}»")

    # --- отчёт ---
    n_jobs = sum(len(metas[m].get("jobs") or []) for m in sources & set(metas))
    print(f"мет обработано : {len(sources)} / {len(metas)}")
    print(f"jobs в своде   : {n_jobs}")
    print(f"тем            : {len(themes)} (лимит {args.limit})")
    print(f"merge_rate     : {1 - len(themes) / n_jobs:.2f}" if n_jobs else "merge_rate     : n/a")
    print(f"болей вне jobs : {len(orphans)}")
    print(f"тегов в словаре: {len(defined)}  использовано: {len(used)}")
    print(f"мотивов        : {len(motives)} / {MOTIVE_LIMIT}")
    if scores:
        srt = sorted(scores.values())
        med = srt[len(srt) // 2] if len(srt) % 2 else (srt[len(srt) // 2 - 1] + srt[len(srt) // 2]) / 2
        print(f"критичность    : макс {max(srt)}, медиана {med:g}, нулевых {srt.count(0)}")
        top = sorted(scores.items(), key=lambda x: -x[1])[:5]
        print("топ по баллу   : " + ", ".join(f"{t} ({s})" for t, s in top))

    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ОШИБКА  {e}")
    print("\nВАЛИДАЦИЯ ПРОЙДЕНА" if not errors else f"\nОШИБОК: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
