"""Render benchmark specifications as realistic PDF and DOCX files.

PDF: lines hard-wrapped at ~90 characters (as a word processor's PDF export
would), 28 lines per page, a running header with the tender reference and a
"Page n of N" footer on every page, so ingestion has to reflow broken
sentences and strip headers/footers.

DOCX: key/value blocks under data-sheet headings and pipe-separated rows (BOQ)
become real Word tables; everything else is one paragraph per line.
"""

from __future__ import annotations

import io
import re
import textwrap
import zipfile
from xml.sax.saxutils import escape

LINES_PER_PAGE = 28
WRAP = 90
TABLE_HEADING = re.compile(r"PARTICULARS|DATA SHEET|PARAMETERS|SCHEDULE OF QUANTITIES|BILL OF QUANTITIES", re.I)


def _pdf_escape(line: str) -> str:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def render_pdf(text: str, running_header: str) -> bytes:
    body: list[str] = []
    for line in text.splitlines():
        body.extend(textwrap.wrap(line, WRAP, break_long_words=False) or [""])
    chunks = [body[i : i + LINES_PER_PAGE] for i in range(0, len(body), LINES_PER_PAGE)]
    total = len(chunks)
    pages = [[running_header, "", *chunk, "", f"Page {n} of {total}"] for n, chunk in enumerate(chunks, 1)]

    objects: list[bytes] = [b"<< /Type /Catalog /Pages 2 0 R >>"]
    page_ids = [3 + 2 * i for i in range(len(pages))]
    font_id = 3 + 2 * len(pages)
    objects.append(f"<< /Type /Pages /Kids [{' '.join(f'{p} 0 R' for p in page_ids)}] /Count {len(pages)} >>".encode())
    for i, lines in enumerate(pages):
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {font_id} 0 R >> >> "
            f"/Contents {page_ids[i] + 1} 0 R >>".encode()
        )
        ops = ["BT", "/F1 9 Tf", "13 TL", "40 800 Td", *[f"({_pdf_escape(line)}) Tj T*" for line in lines], "ET"]
        stream = "\n".join(ops).encode("cp1252", errors="replace")
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, obj in enumerate(objects, 1):
        offsets.append(out.tell())
        out.write(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


def _para(text: str) -> str:
    return f'<w:p><w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def _table(rows: list[list[str]]) -> str:
    cells = "".join("<w:tr>" + "".join(f"<w:tc>{_para(c)}</w:tc>" for c in row) + "</w:tr>" for row in rows)
    return f"<w:tbl>{cells}</w:tbl>"


def render_docx(text: str) -> bytes:
    parts: list[str] = []
    rows: list[list[str]] = []
    in_table_block = False

    def flush() -> None:
        nonlocal rows
        if rows:
            parts.append(_table(rows))
            rows = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
            in_table_block = False
            continue
        if TABLE_HEADING.search(stripped) and ":" not in stripped:
            flush()
            parts.append(_para(stripped))
            in_table_block = True
            continue
        if "|" in stripped:
            rows.append([c.strip() for c in stripped.split("|")])
            continue
        if in_table_block and re.match(r"^[A-Za-z][^:]{1,60}:\s+\S", stripped):
            key, value = stripped.split(":", 1)
            rows.append([key.strip(), value.strip()])
            continue
        flush()
        parts.append(_para(stripped))
    flush()

    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(parts)}</w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        z.writestr("word/document.xml", document)
    return buf.getvalue()
