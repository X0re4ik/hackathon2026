#!/bin/bash
# run-gigacode.sh — Ralph Loop для jobs-merger (адаптация под opencode)
#
# Использование:
#   bash raph-loop-merge-all/run-gigacode.sh
#   nohup bash raph-loop-merge-all/run-gigacode.sh > progress/merge/log.txt 2>&1 &disown
#
# После перехода на gigacode: замени opencode run на gigacode,
# а "--agent build" на "--allowed-tools ... --append-system-prompt ..."

set -eu

# === Каталог скрипта = рабочий каталог ===
WORKDIR="$(cd "$(dirname "$0")" && pwd)"

# === Параметры ===
AGENT="${OPENCODE_AGENT:-build}"           # для opencode; gigacode не использует --agent
META_DIR="${META_DIR:-$WORKDIR/../output/meta}"
SUMMARY="${SUMMARY:-$WORKDIR/../output/OUTPUT.md}"
PROGRESS_DIR="${PROGRESS_DIR:-$WORKDIR/../progress/merge}"
MAX_TURNS="${MAX_TURNS:-30}"

if [ ! -f "$WORKDIR/MAIN_GOAL.md" ]; then
    echo "ОШИБКА: не найден $WORKDIR/MAIN_GOAL.md"
    exit 1
fi

if [ ! -f "$WORKDIR/AGENTS.md" ]; then
    echo "ОШИБКА: не найден $WORKDIR/AGENTS.md"
    exit 1
fi

mkdir -p "$PROGRESS_DIR"

echo "=== Ralph Loop: jobs-merger ==="
echo "  Каталог:      $WORKDIR"
echo "  Меты:         $META_DIR"
echo "  Свод:         $SUMMARY"
echo "  Прогресс:     $PROGRESS_DIR"
echo "  Агент:        $AGENT"
echo "  MAIN_GOAL.md: $WORKDIR/MAIN_GOAL.md"
echo "  AGENTS.md:    $WORKDIR/AGENTS.md"
echo ""

# === Определяем последнюю итерацию по progress/{N}.done.md ===
LAST_ITERATION=0
for f in "$PROGRESS_DIR"/*.done.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .done.md)
    if [[ "$BASENAME" =~ ^[0-9]+$ ]]; then
        [ "$BASENAME" -gt "$LAST_ITERATION" ] && LAST_ITERATION="$BASENAME"
    fi
done

ITERATION=$((LAST_ITERATION + 1))

# === Основной цикл ===
while true; do
    echo "=== Итерация $ITERATION ==="
    echo "  Агент: opencode run --agent $AGENT"
    echo "  PROGRESS_DIR=$PROGRESS_DIR"

    # Проверяем — есть ли META-*.md в папке мет
    META_COUNT=$(ls "$META_DIR"/META-*.md 2>/dev/null | wc -l)
    if [ "$META_COUNT" -eq 0 ]; then
        echo "  Мета-файлы не найдены в $META_DIR — завершение."
        echo "нечего обрабатывать" > "$PROGRESS_DIR/$ITERATION.done.md"
        break
    fi

    # Вызов opencode
    # После перехода на gigacode замени на:
    #   gigacode \
    #       --model "$MODEL" \
    #       --approval-mode=auto-edit \
    #       --allowed-tools "run_shell_command,read_file,write_file" \
    #       --max-session-turns "$MAX_TURNS" \
    #       --append-system-prompt "$WORKDIR/AGENTS.md" \
    #       "Твоя задача описана в $WORKDIR/MAIN_GOAL.md. \
    # PROGRESS_DIR=$PROGRESS_DIR. Текущая итерация: $ITERATION"
    opencode run --agent "$AGENT" "Твоя задача описана в $WORKDIR/MAIN_GOAL.md. \
Прочитай его и выполни шаг за шагом. \
Правила — в $WORKDIR/AGENTS.md. \
PROGRESS_DIR=$PROGRESS_DIR. Текущая итерация: $ITERATION. \
Входная папка мет: $META_DIR. Файл свода: $SUMMARY."

    echo ""
    echo "=== Итерация $ITERATION завершена ==="

    # Выход из цикла, если есть файл goal_done.md
    if [ -f "$PROGRESS_DIR/goal_done.md" ]; then
        echo "  $PROGRESS_DIR/goal_done.md найден — выход из цикла"
        break
    fi

    if [ -f "$PROGRESS_DIR/$ITERATION.done.md" ]; then
        echo "  $PROGRESS_DIR/$ITERATION.done.md найден — переход к итерации $((ITERATION + 1))"
        ITERATION=$((ITERATION + 1))
    else
        echo "  $PROGRESS_DIR/$ITERATION.done.md НЕ найден — повтор итерации $ITERATION"
    fi

    sleep 2
done
