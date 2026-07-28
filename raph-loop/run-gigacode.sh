#!/bin/bash
# run-gigacode.sh — Ralph Loop запускатор для GigaCode (Feature Analyzer)
# Рабочий каталог определяется автоматически как каталог скрипта.
# Ожидается наличие:
#   - MAIN_GOAL.md  — главная цель
#   - AGENTS.md     — промпт агента
#   - progress/     — прогресс-файлы {N}.plan.md / {N}.done.md
#
# Использование: bash run-gigacode.sh [model] [gigacode_args...]
# Примеры:
#   bash run-gigacode.sh
#   bash run-gigacode.sh vllm/DeepSeek-V4-Flash-262k
#   MODEL=vllm/DeepSeek-V4-Flash-262k nohup bash run-gigacode.sh &disown

set -euo pipefail

# === Каталог скрипта = рабочий каталог ===
WORKDIR="$(cd "$(dirname "$0")" && pwd)"

# === Параметры ===
MODEL="${1:-${MODEL:-vllm/DeepSeek-V4-Flash-262k}}"

if [ ! -f "$WORKDIR/MAIN_GOAL.md" ]; then
    echo "ОШИБКА: в каталоге '$WORKDIR' не найден MAIN_GOAL.md"
    echo "Каталог скрипта: $WORKDIR"
    exit 1
fi

if [ ! -f "$WORKDIR/AGENTS.md" ]; then
    echo "ОШИБКА: в каталоге '$WORKDIR' не найден AGENTS.md"
    echo "Каталог скрипта: $WORKDIR"
    exit 1
fi

# === Директории ===
PROGRESS_DIR="$WORKDIR/progress"
mkdir -p "$PROGRESS_DIR"

echo "=== Ralph Loop GigaCode ==="
echo "  Каталог:      $WORKDIR"
echo "  Модель:       $MODEL"
echo "  MAIN_GOAL.md: $WORKDIR/MAIN_GOAL.md"
echo "  AGENTS.md:    $WORKDIR/AGENTS.md"
echo "  Прогресс:     $PROGRESS_DIR"
echo ""

# === Определяем последнюю итерацию по progress/{N}.done.md ===
LAST_ITERATION=0
for f in "$PROGRESS_DIR"/*.done.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .done.md)
    if [[ "$BASENAME" =~ ^[0-9]+$ ]]; then
        if [ "$BASENAME" -gt "$LAST_ITERATION" ]; then
            LAST_ITERATION="$BASENAME"
        fi
    fi
done

ITERATION=$((LAST_ITERATION + 1))

# === Основной цикл ===
while true; do
    echo "=== Итерация $ITERATION ==="
    echo "  Модель: $MODEL"

    export PROGRESS_DIR="$PROGRESS_DIR"

    gigacode \
        --model "$MODEL" \
        --approval-mode=auto-edit \
        --allowed-tools "run_shell_command,read_file,write_file" \
        --max-session-turns 30 \
        --append-system-prompt "$WORKDIR/AGENTS.md" \
        "Твоя задача описана в $WORKDIR/MAIN_GOAL.md. PROGRESS_DIR=$PROGRESS_DIR. Текущая итерация: $ITERATION"

    echo ""
    echo "=== Итерация $ITERATION завершена ==="

    # Выход из цикла, если есть файл goal_done.md
    if [ -f "$PROGRESS_DIR/${ITERATION}.goal_done.md" ]; then
        echo "  Файл $PROGRESS_DIR/${ITERATION}.goal_done.md найден — выход из цикла"
        break
    fi
    
    if [ -f "$PROGRESS_DIR/${ITERATION}.done.md" ]; then
        echo "  Файл $PROGRESS_DIR/${ITERATION}.done.md найден — переход к итерации $((ITERATION + 1))"
        ITERATION=$((ITERATION + 1))
    else
        echo "  Файл $PROGRESS_DIR/${ITERATION}.done.md НЕ найден — повтор итерации $ITERATION"
    fi

    done
