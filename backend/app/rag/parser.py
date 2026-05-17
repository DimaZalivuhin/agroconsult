"""Document parsing for the knowledge-base ingestion pipeline.

Supports PDF, HTML, plain text. The parser returns normalised text with
preserved paragraph boundaries; chunking is done downstream.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.core.logging import get_logger

log = get_logger("parser")

_WHITESPACE = re.compile(r"[\u00A0\s]+")
_MULTI_NEWLINE = re.compile(r"\n{3,}")


def _normalise_text(raw: str) -> str:
    """Collapse runs of whitespace but keep paragraph breaks."""
    paragraphs = []
    for para in raw.split("\n\n"):
        clean = _WHITESPACE.sub(" ", para).strip()
        if clean:
            paragraphs.append(clean)
    text = "\n\n".join(paragraphs)
    return _MULTI_NEWLINE.sub("\n\n", text).strip()


def parse_pdf(path: str | Path) -> str:
    """Extract text from a PDF file page by page."""
    path = Path(path)
    reader = PdfReader(str(path))
    pages: list[str] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
            pages.append(text)
        except Exception as e:  # noqa: BLE001
            log.warning(f"Failed to extract page {i} of {path.name}: {e}")
    return _normalise_text("\n\n".join(pages))


def parse_html(path_or_text: str | Path, *, is_text: bool = False) -> str:
    """Extract text from HTML, removing scripts/styles and inline navigation."""
    if is_text:
        html = str(path_or_text)
    else:
        html = Path(path_or_text).read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return _normalise_text(text)


def parse_txt(path: str | Path) -> str:
    return _normalise_text(Path(path).read_text(encoding="utf-8", errors="ignore"))


def parse_file(path: str | Path) -> str:
    """Dispatch parser by file extension."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(p)
    if suffix in {".html", ".htm"}:
        return parse_html(p)
    if suffix in {".txt", ".md"}:
        return parse_txt(p)
    raise ValueError(f"Unsupported file type: {suffix}")


def parse_bytes(data: bytes, filename: str) -> str:
    """Parse a file given its raw bytes (used for uploaded files)."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        import io

        reader = PdfReader(io.BytesIO(data))
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            try:
                pages.append(page.extract_text() or "")
            except Exception as e:  # noqa: BLE001
                log.warning(f"Failed to extract page {i} of {filename}: {e}")
        return _normalise_text("\n\n".join(pages))
    if suffix in {".html", ".htm"}:
        return parse_html(data.decode("utf-8", errors="ignore"), is_text=True)
    if suffix in {".txt", ".md"}:
        return _normalise_text(data.decode("utf-8", errors="ignore"))
    raise ValueError(f"Unsupported file type: {suffix}")


# ---------- Structural hints ----------
_STRUCTURE_PATTERNS = [
    (re.compile(r"^(Раздел\s+[IVXLC0-9]+\.?\s.*)$", re.MULTILINE | re.IGNORECASE), "section"),
    (re.compile(r"^(Глава\s+\d+\.?\s.*)$", re.MULTILINE | re.IGNORECASE), "chapter"),
    (re.compile(r"^(Статья\s+\d+\.?\s.*)$", re.MULTILINE | re.IGNORECASE), "article"),
    (re.compile(r"^(\d+\.\s.*)$", re.MULTILINE), "paragraph"),
]


def detect_section_path(snippet: str) -> str | None:
    """Best-effort detection of the structural anchor for a chunk."""
    parts: list[str] = []
    for pattern, _name in _STRUCTURE_PATTERNS:
        m = pattern.search(snippet)
        if m:
            parts.append(m.group(1).strip()[:120])
    return " / ".join(parts) if parts else None


def iter_paragraphs(text: str) -> Iterable[str]:
    for para in text.split("\n\n"):
        para = para.strip()
        if para:
            yield para
