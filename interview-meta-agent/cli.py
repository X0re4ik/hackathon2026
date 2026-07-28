"""CLI-интерфейс для Interview Meta Agent.

Используется host-агентом (GigaCode/Cursor/opencode) как интерфейс:
  cli.py convert <path>       — прочитать файл, вернуть текст + source
  cli.py validate '<json>'    — валидировать мету по схеме
  cli.py save '<json>'        — сохранить мету в .md

Режим B: интеллект в SKILL.md, CLI — только детерминированные операции.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from core.convert import convert_source
from core.renderer import render_markdown, validate_meta
from core.schema import InterviewMeta


def cmd_convert(args: list[str]):
    path = args[0]
    if not Path(path).exists():
        print(json.dumps({"ok": False, "error": f"file not found: {path}"}, ensure_ascii=False))
        return

    text, source = convert_source(path)
    meta_id = InterviewMeta.compute_meta_id(Path(path).read_bytes())
    print(json.dumps({
        "ok": True,
        "meta_id": meta_id,
        "text": text,
        "source": source.model_dump(mode="json"),
    }, ensure_ascii=False, indent=2))


def cmd_validate(args: list[str]):
    try:
        data = json.loads(args[0])
    except (IndexError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return

    result = validate_meta(data)
    print(json.dumps({
        "ok": result.valid,
        "errors": [e.model_dump() for e in result.errors],
    }, ensure_ascii=False, indent=2))


def cmd_save(args: list[str]):
    try:
        data = json.loads(args[0])
        meta = InterviewMeta(**data)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return

    try:
        md = render_markdown(meta)
        out_dir = Path("output/meta")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{meta.meta_id}.md"
        out_path.write_text(md, encoding="utf-8")
        print(json.dumps({"ok": True, "path": str(out_path)}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  cli.py convert <path>        — read file -> text + source")
        print("  cli.py validate '<json>'     — validate extracted meta")
        print("  cli.py save '<json>'         — save meta as .md")
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "convert": cmd_convert,
        "validate": cmd_validate,
        "save": cmd_save,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print("Available: convert, validate, save")
        sys.exit(1)

    commands[command](args)


if __name__ == "__main__":
    main()
