#!/usr/bin/env python3
"""Графики по метаданным интервью и тикетов бэклога (output/meta/META-*.md).

Читает YAML-frontmatter всех META-файлов и строит PNG-графики в output/charts/:
  - segments.png    — распределение по типам клиентов (сегменты)
  - pain_nature.png — природа болей: интервью vs бэклог (stacked)
  - trust.png       — боли, подрывающие доверие (trust_breach)
  - emotions.png    — эмоциональный окрас болей из интервью
  - frequency.png   — частота болей из интервью
  - engagement.png  — вовлечённость и статус респондентов
  - dashboard.png   — сводный дашборд 2x3
Заодно печатает сводку метрик в stdout.
"""
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml

ROOT = Path(__file__).resolve().parent.parent
META_DIR = ROOT / "output" / "meta"
CHARTS_DIR = ROOT / "output" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

NATURE_ORDER = ["missing_feature", "defect", "ux_friction", "trust_breach", "expectation_mismatch"]
NATURE_RU = {
    "missing_feature": "нет фичи",
    "defect": "дефект",
    "ux_friction": "UX-трение",
    "trust_breach": "подрыв доверия",
    "expectation_mismatch": "разрыв ожиданий",
}
SEGMENT_RU = {
    "individual": "Физлицо",
    "sole_proprietor": "ИП",
    "business": "Бизнес",
    "unknown": "Не определён",
}
FREQ_ORDER = ["daily", "weekly", "monthly", "rare"]
FREQ_RU = {"daily": "ежедневно", "weekly": "еженедельно", "monthly": "ежемесячно", "rare": "редко"}
STATUS_RU = {"churned": "ушёл", "churning": "уходит", "active": "активен", "new": "новый"}
C_INT, C_BACK, C_ACC = "#2b7bbb", "#f0a03c", "#c94f4f"


def load_meta():
    records = []
    for path in sorted(META_DIR.glob("META-*.md")):
        text = path.read_text(encoding="utf-8")
        parts = text.split("---\n", 2)
        if len(parts) < 3:
            continue
        meta = yaml.safe_load(parts[1])
        meta["_file"] = path.name
        meta["_kind"] = "interview" if "INT-T" in path.name else "backlog"
        records.append(meta)
    return records


def pains_of(meta):
    for p in meta.get("pains") or []:
        p["_kind"] = meta["_kind"]
        yield p


def bar_values(ax, bars):
    for b in bars:
        h = b.get_height()
        if h:
            ax.text(b.get_x() + b.get_width() / 2, h, str(int(h)),
                    ha="center", va="bottom", fontsize=10)


def fig_segments(records, ax):
    counts = Counter()
    for m in records:
        seg = (m.get("segment") or {}).get("type")
        if m["_kind"] == "backlog" and not seg:
            counts["без сегмента\n(бэклог)"] += 1
        else:
            counts[SEGMENT_RU.get(seg or "unknown", seg)] += 1
    labels = list(counts.keys())
    bars = ax.bar(labels, [counts[k] for k in labels], color=C_INT)
    bar_values(ax, bars)
    ax.set_title("Типы клиентов (по файлам)")
    ax.set_ylabel("файлов")


def fig_pain_nature(records, ax):
    cnt = {"interview": Counter(), "backlog": Counter()}
    for m in records:
        for p in pains_of(m):
            nature = ((p.get("commentary") or {}).get("pain_nature")) or "unknown"
            cnt[p["_kind"]][nature] += 1
    xs = range(len(NATURE_ORDER))
    b1 = ax.bar(xs, [cnt["interview"][n] for n in NATURE_ORDER],
                label="интервью", color=C_INT)
    b2 = ax.bar(xs, [cnt["backlog"][n] for n in NATURE_ORDER],
                bottom=[cnt["interview"][n] for n in NATURE_ORDER],
                label="бэклог", color=C_BACK)
    bar_values(ax, b1)
    for b, n in zip(b2, NATURE_ORDER):
        total = cnt["interview"][n] + cnt["backlog"][n]
        if total:
            ax.text(b.get_x() + b.get_width() / 2, total, str(total),
                    ha="center", va="bottom", fontsize=10)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([NATURE_RU[n] for n in NATURE_ORDER], fontsize=9,
                       rotation=15, ha="right")
    ax.set_title("Природа болей")
    ax.set_ylabel("болей")
    ax.legend()


def fig_trust(records, ax):
    cnt = {"interview": [0, 0], "backlog": [0, 0]}  # [trust, no_trust]
    for m in records:
        for p in pains_of(m):
            cnt[p["_kind"]][0 if p.get("trust_breach") else 1] += 1
    xs = range(2)
    b1 = ax.bar(xs, [cnt["interview"][0], cnt["backlog"][0]], color=C_ACC,
                tick_label=["интервью", "бэклог"])
    bar_values(ax, b1)
    ax.set_title("Боли, подрывающие доверие (trust_breach)")
    ax.set_ylabel("болей")
    for i, k in enumerate(["interview", "backlog"]):
        total = sum(cnt[k])
        share = cnt[k][0] / total * 100 if total else 0
        ax.text(i, cnt[k][0] / 2, f"{share:.0f}%\nот всех болей", ha="center",
                va="center", fontsize=9, color="white", fontweight="bold")


def fig_emotions(records, ax):
    counts = Counter()
    for m in records:
        if m["_kind"] != "interview":
            continue
        for p in pains_of(m):
            v = ((p.get("emotion") or {}).get("valence"))
            if v is not None:
                counts[v] += 1
    xs = sorted(counts)
    colors = ["#c94f4f" if x < 0 else "#7f7f7f" if x == 0 else "#4f9c4f" for x in xs]
    bars = ax.bar([str(x) for x in xs], [counts[x] for x in xs], color=colors)
    bar_values(ax, bars)
    ax.set_title("Эмоциональный окрас болей (интервью)")
    ax.set_xlabel("valence (-2 … +2)")
    ax.set_ylabel("болей")


def fig_frequency(records, ax):
    counts = Counter()
    for m in records:
        if m["_kind"] != "interview":
            continue
        for p in pains_of(m):
            f = p.get("frequency")
            if f in FREQ_ORDER:
                counts[f] += 1
    bars = ax.bar([FREQ_RU[f] for f in FREQ_ORDER],
                  [counts[f] for f in FREQ_ORDER], color=C_INT)
    bar_values(ax, bars)
    ax.set_title("Частота болей (интервью)")
    ax.set_ylabel("болей")


def fig_engagement(records, ax):
    people = []
    for m in records:
        if m["_kind"] != "interview":
            continue
        eng = m.get("engagement") or {}
        status = (m.get("respondent") or {}).get("customer_status")
        people.append((m["meta_id"].replace("META-INT-", ""),
                       eng.get("engagement_score") or 0, status))
    people.sort(key=lambda x: x[1], reverse=True)
    colors = {"churned": C_ACC, "churning": "#e08a3c", "active": "#4f9c4f", "new": C_INT}
    bars = ax.bar([p[0] for p in people], [p[1] for p in people],
                  color=[colors.get(p[2], "#7f7f7f") for p in people])
    bar_values(ax, bars)
    ax.set_title("Вовлечённость респондентов (0–10)")
    ax.set_ylabel("engagement score")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
    ax.legend(handles, [STATUS_RU[s] for s in colors], fontsize=8)


FIGS = [
    ("segments.png", fig_segments),
    ("pain_nature.png", fig_pain_nature),
    ("trust.png", fig_trust),
    ("emotions.png", fig_emotions),
    ("frequency.png", fig_frequency),
    ("engagement.png", fig_engagement),
]


def print_metrics(records):
    interviews = [m for m in records if m["_kind"] == "interview"]
    backlog = [m for m in records if m["_kind"] == "backlog"]
    all_pains = [p for m in records for p in pains_of(m)]
    int_pains = [p for p in all_pains if p["_kind"] == "interview"]
    trust = [p for p in all_pains if p.get("trust_breach")]
    print("\n===== МЕТРИКИ =====")
    print(f"файлов меты: {len(records)} (интервью {len(interviews)}, бэклог {len(backlog)})")
    print(f"болей всего: {len(all_pains)} (интервью {len(int_pains)}, "
          f"бэклог {len(all_pains) - len(int_pains)})")
    print(f"trust_breach: {len(trust)} ({len(trust) / len(all_pains) * 100:.0f}%)")
    jobs = sum(len(m.get("jobs") or []) for m in records)
    print(f"JTBD всего: {jobs}")
    statuses = Counter((m.get("respondent") or {}).get("customer_status") for m in interviews)
    print("статусы респондентов:", dict(statuses))


def main():
    records = load_meta()
    print(f"загружено META-файлов: {len(records)}")

    for fname, draw in FIGS:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        draw(records, ax)
        fig.tight_layout()
        fig.savefig(CHARTS_DIR / fname, dpi=150)
        plt.close(fig)
        print(f"OK  {fname}")

    fig, axes = plt.subplots(2, 3, figsize=(18, 9))
    for (_, draw), ax in zip(FIGS, axes.flat):
        draw(records, ax)
    fig.suptitle("Метаданные интервью и бэклога — сводный дашборд", fontsize=14)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "dashboard.png", dpi=150)
    plt.close(fig)
    print("OK  dashboard.png")

    print_metrics(records)


if __name__ == "__main__":
    main()
