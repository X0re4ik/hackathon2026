from pathlib import Path

from core.schema import Source


def convert_source(path: str) -> tuple[str, Source]:
    p = Path(path)
    content = p.read_text(encoding="utf-8")
    source = Source(
        origin="user_transcript" if p.suffix == ".txt" else str(p.suffix),
        modality="text",
        reference=str(p.absolute()),
        attributes={"filename": p.name, "size_bytes": len(content)},
    )
    return content, source
