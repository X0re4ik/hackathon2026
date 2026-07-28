import re
import zipfile
from pathlib import Path

from core.schema import Source


def _extract_docx_text(path: str) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    xml = re.sub(r"</w:p>", "\n", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    import html
    return html.unescape(text).strip()


def convert_source(path: str) -> tuple[str, Source]:
    p = Path(path)

    suffix = p.suffix.lower()
    if suffix == ".docx":
        content = _extract_docx_text(str(p))
        origin = "user_interview_docx"
    else:
        content = p.read_text(encoding="utf-8")
        origin = "user_transcript" if suffix == ".txt" else str(suffix)

    source = Source(
        origin=origin,
        modality="text",
        reference=str(p.absolute()),
        attributes={"filename": p.name, "size_bytes": len(content)},
    )
    return content, source
