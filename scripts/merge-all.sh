#!/bin/bash
# merge-all.sh — Ralph Loop для jobs-merger.
#
# Одна итерация = одна мета = один запуск подагента с чистым контекстом.
# Скрипт сам находит следующий необработанный файл и передаёт его агенту явно.
# Агент ничего не выбирает: он получает путь и обрабатывает его.
#
# Прогресс: progress/merge/{N}.plan.md → {N}.done.md, в конце goal_done.md.
# Цикл возобновляемый: источник истины — sources[] в файле свода, а не счётчик.
#
# Использование:
#   bash scripts/merge-all.sh
#   bash scripts/merge-all.sh output/meta output/OUTPUT.md
#   nohup bash scripts/merge-all.sh > progress/merge/log.txt 2>&1 &disown

set -euo pipefail

META_DIR="${1:-output/meta}"
SUMMARY="${2:-output/OUTPUT.md}"
SKILL_DIR="${SKILL_DIR:-.opencode/skills/jobs-merger}"
PROGRESS_DIR="${PROGRESS_DIR:-progress/merge}"
AGENT="${AGENT:-jobs-merger}"
MAX_RETRY="${MAX_RETRY:-2}"

# === Проверки окружения ===
command -v opencode >/dev/null 2>&1 || { echo "ОШИБКА: opencode не найден в PATH"; exit 1; }
command -v python3  >/dev/null 2>&1 || { echo "ОШИБКА: python3 не найден в PATH"; exit 1; }
[ -d "$META_DIR" ] || { echo "ОШИБКА: каталог мет не найден: $META_DIR"; exit 1; }
[ -f "$SKILL_DIR/finalization.md" ] || {
    echo "ОШИБКА: не найден $SKILL_DIR/finalization.md"
    echo "Укажи путь к скиллу: SKILL_DIR=... bash scripts/merge-all.sh"
    exit 1
}

mkdir -p "$PROGRESS_DIR" "$(dirname "$SUMMARY")"

# === Хелперы ===

# Печатает две строки — путь и meta_id первой меты, которой нет в sources[] свода.
# Пусто, если обработаны все. Frontmatter парсится строго до второго '---'.
next_meta() {
    python3 - "$META_DIR" "$SUMMARY" <<'PY'
import os, re, sys

meta_dir, summary = sys.argv[1], sys.argv[2]

def frontmatter(path):
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return ""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""

done = set(re.findall(r"^\s*-?\s*meta_id:\s*(\S+)", frontmatter(summary), re.M))

for name in sorted(os.listdir(meta_dir)):
    if not (name.startswith("META-") and name.endswith(".md")):
        continue
    path = os.path.join(meta_dir, name)
    found = re.search(r"^\s*meta_id:\s*(\S+)", frontmatter(path), re.M)
    mid = found.group(1) if found else os.path.splitext(name)[0]
    if mid not in done:
        print(path)
        print(mid)
        break
PY
}

# Код 0, если meta_id уже в sources[] свода.
in_sources() {
    python3 - "$SUMMARY" "$1" <<'PY'
import re, sys

summary, mid = sys.argv[1], sys.argv[2]
try:
    text = open(summary, encoding="utf-8").read()
except OSError:
    sys.exit(1)
if not text.startswith("---"):
    sys.exit(1)
end = text.find("\n---", 3)
fm = text[3:end] if end != -1 else ""
sys.exit(0 if mid in re.findall(r"^\s*-?\s*meta_id:\s*(\S+)", fm, re.M) else 1)
PY
}

count_glob() {
    local c=0 f
    for f in $1; do [ -f "$f" ] && c=$((c + 1)); done
    echo "$c"
}

TOTAL=$(count_glob "$META_DIR/META-*.md")
[ "$TOTAL" -gt 0 ] || { echo "Мета-файлы META-*.md не найдены в $META_DIR"; exit 1; }

# Номер итерации продолжает нумерацию прошлых запусков.
N=0
for f in "$PROGRESS_DIR"/*.done.md; do
    [ -f "$f" ] || continue
    bn=$(basename "$f" .done.md)
    [[ "$bn" =~ ^[0-9]+$ ]] && [ "$bn" -gt "$N" ] && N="$bn"
done
N=$((N + 1))

echo "=== Ralph Loop: jobs-merger ==="
echo "  Меты:      $META_DIR ($TOTAL шт.)"
echo "  Свод:      $SUMMARY"
echo "  Скилл:     $SKILL_DIR"
echo "  Прогресс:  $PROGRESS_DIR"
echo "  Агент:     $AGENT"
echo "  Итерация:  $N"
echo ""

RETRY=0
PREV_ID=""

# === Основной цикл ===
while true; do
    FILE=""; MID=""
    { read -r FILE || true; read -r MID || true; } < <(next_meta)

    # --- Все меты обработаны: финализация и выход ---
    if [ -z "$FILE" ]; then
        if [ -f "$PROGRESS_DIR/goal_done.md" ]; then
            echo "Все меты уже обработаны, финализация была выполнена ранее."
            echo "Чтобы прогнать финализацию заново: rm $PROGRESS_DIR/goal_done.md"
            exit 0
        fi

        echo "============================================="
        echo "▶ ВСЕ $TOTAL МЕТ ОБРАБОТАНЫ — ФИНАЛИЗАЦИЯ"
        echo "============================================="

        printf 'Итерация: %s\nФайл: (нет)\nДействие: финализация свода\n' \
            "$N" > "$PROGRESS_DIR/$N.plan.md"

        opencode run --agent "$AGENT" "Цикл слияния закончен, все меты обработаны. \
Выполни финализацию файла свода $SUMMARY. Прочитай $SKILL_DIR/finalization.md \
и выполни его целиком, по шагам. На финализации правило 1 снято: свод читай полностью, \
арифметика по всему файлу разрешена."

        printf 'Финализация выполнена. Мет обработано: %s\n' \
            "$TOTAL" > "$PROGRESS_DIR/$N.done.md"
        printf 'Все меты из %s обработаны.\nОбработано: %s\nСвод: %s\n' \
            "$META_DIR" "$TOTAL" "$SUMMARY" > "$PROGRESS_DIR/goal_done.md"

        echo ""
        echo "Цикл завершён. Записан $PROGRESS_DIR/goal_done.md"

        if [ -f "$SKILL_DIR/scripts/validate.py" ]; then
            echo ""
            echo "=== Валидация ==="
            python3 "$SKILL_DIR/scripts/validate.py" \
                --meta "$META_DIR" --summary "$SUMMARY" || {
                echo ""
                echo "⚠ Валидатор нашёл расхождения — см. вывод выше."
                exit 2
            }
        fi
        exit 0
    fi

    # --- Защита от вечного цикла: та же мета пришла снова ---
    if [ "$MID" = "$PREV_ID" ]; then
        RETRY=$((RETRY + 1))
        if [ "$RETRY" -gt "$MAX_RETRY" ]; then
            echo ""
            echo "ОСТАНОВ: $MID не попал в sources[] за $((MAX_RETRY + 1)) попыток."
            echo "Смотри $SUMMARY и лог агента — итерация не доводится до конца."
            printf 'Итерация: %s\nФайл: %s\nmeta_id: %s\nСтатус: провал после %s попыток\n' \
                "$N" "$FILE" "$MID" "$((MAX_RETRY + 1))" > "$PROGRESS_DIR/$N.failed.md"
            exit 1
        fi
        echo "  ⚠ повтор итерации $N для $MID — попытка $((RETRY + 1)) из $((MAX_RETRY + 1))"
    else
        RETRY=0
        PREV_ID="$MID"
    fi

    DONE=$(count_glob "$PROGRESS_DIR/*.done.md")

    echo "============================================="
    echo "▶ ИТЕРАЦИЯ $N — $MID   [обработано $DONE из $TOTAL]"
    echo "============================================="
    echo "  Файл: $FILE"

    printf 'Итерация: %s\nФайл: %s\nmeta_id: %s\nДействие: слияние одной меты в свод\n' \
        "$N" "$FILE" "$MID" > "$PROGRESS_DIR/$N.plan.md"

    opencode run --agent "$AGENT" "Выполни ровно одну итерацию слияния. \
Входной мета-файл: $FILE. Файл свода: $SUMMARY. \
Файл выбран за тебя — не ищи другие меты и не проверяй sources[] на повтор. \
Соблюдай правило 1: читай эту мету, а из свода только frontmatter, таблицу тем \
и секции тех тем, которые трогаешь. Разделы «Облако тегов» и «Критичность» не трогай. \
Закончив, выдай отчёт на четыре строки."

    # --- Проверка: агент действительно дописал мету в sources[] ---
    if in_sources "$MID"; then
        printf '%s → ✅ обработан\nmeta_id: %s\n' \
            "$FILE" "$MID" > "$PROGRESS_DIR/$N.done.md"
        echo "  → $PROGRESS_DIR/$N.done.md"
        N=$((N + 1))
    else
        echo "  ⚠ $MID не появился в sources[] — done.md не записан, итерация повторится"
    fi

    sleep 2
done
