"""Document parsing: PDF (pypdf), DOCX (mammoth) and plain text."""

from __future__ import annotations

import html
import io
import re
from typing import Callable, Optional, Union

from ..types import ParsedDocument, ParsedPage
from .normalize import normalize_characters, reflow_lines, strip_repeated_lines

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_TEXT_CHARS = 1_000_000
# Below this many extracted characters per page a PDF is treated as scanned.
MIN_CHARS_PER_PAGE = 40

PDF_PARSER = "pypdf"
DOCX_PARSER = "mammoth"


class ParseError(Exception):
    """A document that cannot be analysed. ``code`` is stable and shown to clients."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def detect_format(filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else None
    magic = data[:5]
    if magic.startswith(b"%PDF"):
        return "pdf"
    if magic.startswith(b"PK"):
        if ext and ext != "docx":
            raise ParseError("unsupported_format", f"Only .docx archives are supported (got .{ext}).")
        return "docx"
    if ext == "txt":
        return "txt"
    if ext == "pdf":
        raise ParseError("corrupt", "The file has a .pdf extension but is not a valid PDF.")
    if ext == "docx":
        raise ParseError("corrupt", "The file has a .docx extension but is not a valid Word document.")
    raise ParseError("unsupported_format", "Unsupported file. Upload PDF, DOCX, or TXT.")


def _parse_pdf(data: bytes) -> list[str]:
    from pypdf import PdfReader
    from pypdf.errors import FileNotDecryptedError, PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            # Owner-password-only PDFs open with an empty user password.
            if not reader.decrypt(""):
                raise ParseError("encrypted", "The PDF is password-protected. Remove the password and upload again.")
        return [page.extract_text() or "" for page in reader.pages]
    except ParseError:
        raise
    except FileNotDecryptedError as exc:
        raise ParseError("encrypted", "The PDF is password-protected. Remove the password and upload again.") from exc
    except (PdfReadError, ValueError, KeyError, TypeError) as exc:
        if re.search(r"password|encrypt", str(exc), re.I):
            raise ParseError("encrypted", "The PDF is password-protected. Remove the password and upload again.") from exc
        raise ParseError("corrupt", "The PDF could not be read. It may be damaged.") from exc


def _parse_docx(data: bytes) -> str:
    import mammoth

    try:
        result = mammoth.convert_to_html(io.BytesIO(data))
    except Exception as exc:  # mammoth raises zipfile/KeyError/ValueError subclasses on damage
        raise ParseError("corrupt", "The Word document could not be read. It may be damaged.") from exc
    return docx_html_to_text(result.value)


_TAG = re.compile(r"<[^>]+>")


def _strip_tags(value: str) -> str:
    return _TAG.sub("", value)


def docx_html_to_text(markup: str) -> str:
    """Turn mammoth's HTML into lines.

    Mammoth emits a small, well-formed HTML subset (p, h1–h6, ul/ol/li, table,
    strong/em). Headings and list items stay on their own lines, and
    two-column table rows become "Parameter: Value" lines, which is how
    procurement specifications usually tabulate technical data.
    """

    def row(match: re.Match[str]) -> str:
        cells = [
            _strip_tags(m.group(1)).strip()
            for m in re.finditer(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", match.group(1), re.I)
        ]
        cells = [c for c in cells if c]
        if len(cells) == 2:
            return f"\n{cells[0]}: {cells[1]}\n"
        return f"\n{' | '.join(cells)}\n"

    text = re.sub(r"<tr[^>]*>([\s\S]*?)</tr>", row, markup, flags=re.I)
    text = re.sub(r"<li[^>]*>", "\n• ", text, flags=re.I)
    text = re.sub(r"</(p|h[1-6]|li|ul|ol|table)>", "\n", text, flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    return html.unescape(_strip_tags(text))


def decode_text(data: bytes) -> str:
    body = data[3:] if data[:3] == b"\xef\xbb\xbf" else data
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return body.decode("cp1252", errors="replace")


def _assemble(fmt: str, parser: str, raw_pages: list[str], warnings: list[str]) -> ParsedDocument:
    cleaned = [reflow_lines(p) for p in strip_repeated_lines([normalize_characters(p) for p in raw_pages])]
    pages = [ParsedPage(number=i + 1, text=t) for i, t in enumerate(cleaned)]
    text = "\n\n".join(p.text for p in pages)
    if not text.strip():
        raise ParseError("empty", "No readable text was found in the document.")
    if len(text) > MAX_TEXT_CHARS:
        raise ParseError(
            "too_long", f"The document has {len(text):,} characters; the limit is {MAX_TEXT_CHARS:,}."
        )
    return ParsedDocument(format=fmt, parser=parser, pages=pages, text=text, warnings=warnings)


def parse_text(text: str) -> ParsedDocument:
    if not text.strip():
        raise ParseError("empty", "Add a document or specification text first.")
    return _assemble("text", "plain-text", [text], [])


def parse_bytes(data: bytes, filename: str) -> ParsedDocument:
    if len(data) == 0:
        raise ParseError("empty", "The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ParseError("too_large", "Upload failed. The maximum file size is 20 MB.")
    fmt = detect_format(filename, data)
    warnings: list[str] = []
    if fmt == "pdf":
        pages = _parse_pdf(data)
        chars = sum(len(re.sub(r"\s", "", p)) for p in pages)
        if chars / max(1, len(pages)) < MIN_CHARS_PER_PAGE:
            raise ParseError(
                "no_text_layer",
                "This PDF appears to be scanned (no text layer). OCR is not supported yet; "
                "upload a text-based PDF, DOCX, or TXT.",
            )
        sparse = sum(1 for p in pages if len(re.sub(r"\s", "", p)) < MIN_CHARS_PER_PAGE)
        if sparse:
            warnings.append(
                f"{sparse} page(s) had little or no extractable text and may be scanned images; "
                "their content was not analysed."
            )
        return _assemble("pdf", PDF_PARSER, pages, warnings)
    if fmt == "docx":
        return _assemble("docx", DOCX_PARSER, [_parse_docx(data)], warnings)
    return _assemble("txt", "utf-8", [decode_text(data)], warnings)


def parse_document(source: Union[str, tuple[bytes, str]]) -> ParsedDocument:
    """Parse pasted text (``str``) or an upload (``(bytes, filename)``)."""
    if isinstance(source, str):
        return parse_text(source)
    data, filename = source
    return parse_bytes(data, filename)


def page_locator(doc: ParsedDocument) -> Callable[[int], Optional[int]]:
    """Map a character offset in ``doc.text`` to its 1-based page, or None for single-page sources."""
    if doc.format != "pdf":
        return lambda _offset: None
    starts: list[int] = []
    cursor = 0
    for page in doc.pages:
        starts.append(cursor)
        cursor += len(page.text) + 2

    def locate(offset: int) -> Optional[int]:
        page = 1
        for i, start in enumerate(starts):
            if start <= offset:
                page = i + 1
        return page

    return locate
