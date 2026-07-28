from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.convert import convert_source
from core.renderer import render_markdown, validate_meta
from core.schema import InterviewMeta

load_dotenv()

mcp = FastMCP("interview-meta-agent")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output/meta")


@mcp.tool()
async def convert_source(path: str) -> dict:
    """Читает текстовый файл и возвращает содержимое + блок source.

    Args:
        path: путь к файлу (относительный или абсолютный).
    """
    p = Path(path)
    if not p.exists():
        resolved = Path.cwd() / path
        if not resolved.exists():
            return {"ok": False, "error": f"file not found: {path}"}
        p = resolved

    try:
        text, source = convert_source(str(p))
        return {
            "ok": True,
            "text": text,
            "source": source.model_dump(mode="json"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@mcp.tool()
async def validate_meta(meta_json: str) -> dict:
    """Валидирует извлечённую метаинформацию по Pydantic-схеме.

    Args:
        meta_json: JSON-строка с извлечёнными метаданными.
    """
    try:
        data = json.loads(meta_json)
    except json.JSONDecodeError as e:
        return {"ok": False, "errors": [{"field": "json", "message": f"invalid JSON: {e}"}]}

    result = validate_meta(data)
    return {"ok": result.valid, "errors": [e.model_dump() for e in result.errors]}


@mcp.tool()
async def save_meta(meta_json: str) -> dict:
    """Сохраняет валидную метаинформацию в .md файл.

    Args:
        meta_json: JSON-строка с валидными метаданными.
    """
    try:
        data = json.loads(meta_json)
        meta = InterviewMeta(**data)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    try:
        md = render_markdown(meta)
        out_dir = Path(OUTPUT_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{meta.meta_id}.md"
        out_path.write_text(md, encoding="utf-8")
        return {"ok": True, "path": str(out_path)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    if transport == "http":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        host = sys.argv[3] if len(sys.argv) > 3 else "0.0.0.0"
        mcp.run(transport="sse", host=host, port=port)
    else:
        mcp.run(transport="stdio")
