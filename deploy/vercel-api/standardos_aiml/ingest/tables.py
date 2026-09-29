"""Turn pipe tables into one statement per row (non-specification documents).

Datasheets, test certificates, lab reports and BOQs carry their content in tables
whose unit sits in its own column ("Turbidity | NTU | 3.2 | 1"), so a value is never
next to its unit and the row is not a sentence. This rewrites each data row using the
header to name its columns:

    Sl. No. | Particulars | Unit | Offered          →  Rated power: 630 kVA.
    1       | Rated power | kVA  | 630

    Parameter | Unit | Result | Acceptable limit  →  Turbidity: result 3.2 NTU; acceptable limit 1 NTU.

    Test | Requirement | Observed | Result          →  Insulation resistance: requirement Min 100 Mohm-km;
                                                         observed 2400 Mohm-km; Pass.

Rows are rewritten in place (one line per row), so the rest of the pipeline reads them
like any other statement. Used when ``PipelineConfig.tables_v2`` is on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PIPE_ROW = re.compile(r"^\s*\|?[^|\n]*\|[^|\n]*\|")  # at least three cells
NUMERIC = re.compile(r"^[\s(]*(?:max\.?|min\.?|≤|≥|<|>)?\s*[-+]?\d[\d.,]*(?:\s*(?:/|-|–|to)\s*[-+]?\d[\d.,]*)?[\s)]*$", re.I)
VERDICT = re.compile(
    r"^(pass(ed)?|fail(ed)?|ok|complied|not complied|complies|does not comply|withstood|satisfactory|"
    r"unsatisfactory|conforms?|not conforming|accepted|rejected|within limits?|nil)$",
    re.I,
)

SERIAL_H = re.compile(r"^(s\.?\s*no\.?|sl\.?\s*no\.?|sr\.?\s*no\.?|no\.?|#|item(\s*no\.?)?)$", re.I)
PARAM_H = re.compile(r"particular|parameter|description|characteristic|property|test|item|specification|details", re.I)
UNIT_H = re.compile(r"^(unit|units|uom|unit of measure(ment)?)$", re.I)
QTY_H = re.compile(r"^(qty\.?|quantity|nos?\.?)$", re.I)
LIMIT_H = re.compile(r"requirement|specified|limit|permissible|acceptable|required|guaranteed|standard value|max|min", re.I)
OBS_H = re.compile(r"result|observed|measured|actual|found|offered|declared|obtained|value|reading", re.I)
SKIP_H = re.compile(r"^(rate|amount|price|cost|make|brand|remarks?)$", re.I)


@dataclass
class Column:
    header: str
    role: str  # serial | param | unit | qty | limit | observed | verdict | other | skip


def _cells(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [c.strip() for c in body.split("|")]


def _is_header(cells: list[str]) -> bool:
    filled = [c for c in cells if c]
    if len(filled) < 2:
        return False
    numeric = sum(1 for c in filled if NUMERIC.match(c))
    keyword = any(
        PARAM_H.search(c) or UNIT_H.match(c) or LIMIT_H.search(c) or OBS_H.search(c) or QTY_H.match(c)
        for c in filled
    )
    return numeric == 0 and keyword


def _roles(header: list[str], rows: list[list[str]]) -> list[Column]:
    cols: list[Column] = []
    for i, h in enumerate(header):
        values = [r[i] for r in rows if i < len(r) and r[i]]
        role = "other"
        if values and all(VERDICT.match(v) for v in values):
            role = "verdict"
        elif SERIAL_H.match(h) and all(re.fullmatch(r"[\w.()]{1,5}", v) for v in values):
            role = "serial"
        elif UNIT_H.match(h):
            role = "unit"
        elif QTY_H.match(h):
            role = "qty"
        elif SKIP_H.match(h):
            role = "skip"
        elif LIMIT_H.search(h) and not re.search(r"offered|result|observed|measured", h, re.I):
            role = "limit"
        elif OBS_H.search(h):
            role = "observed"
        elif PARAM_H.search(h):
            role = "param"
        cols.append(Column(h, role))
    if not any(c.role == "param" for c in cols):
        # The first mostly-textual column names the row.
        for i, c in enumerate(cols):
            values = [r[i] for r in rows if i < len(r) and r[i]]
            if c.role in ("other", "observed") and values and sum(bool(NUMERIC.match(v)) for v in values) <= len(values) / 3:
                c.role = "param"
                break
    return cols


def _label(header: str) -> str:
    """Column header as an in-sentence label; keeps "IS 10500:2012" and other capitals intact."""
    h = header.strip()
    return h[0].lower() + h[1:] if len(h) > 1 and h[0].isupper() and h[1].islower() else h


LEADING_NUMBER = re.compile(r"^(\s*[-+]?\d[\d.,]*(?:\s*(?:/|-|–|to)\s*[-+]?\d[\d.,]*)?)(\s+(?:for|at|x|×|@|over|with)\b.*)$", re.I)


def _with_unit(value: str, unit: str) -> str:
    if not unit or unit in ("-", "—", "–"):
        return value
    if NUMERIC.match(value):
        return f"{value} {unit}"
    # "50 for 1 s" in a kA column → "50 kA for 1 s"
    m = LEADING_NUMBER.match(value)
    return f"{m.group(1)} {unit}{m.group(2)}" if m else value


def _row_text(cols: list[Column], cells: list[str]) -> str | None:
    get = lambda role: [(c, cells[i]) for i, c in enumerate(cols) if c.role == role and i < len(cells) and cells[i]]
    params = get("param")
    if not params:
        return None
    name = params[0][1].rstrip(":")
    serial = next((v for _, v in get("serial")), None)
    if re.match(r"\d", name):
        # "3.5 core 300 sq mm …" would otherwise read as clause 3.5.
        name = f"Item {serial}: {name}" if serial else f"Item: {name}"
    unit = next((v for _, v in get("unit")), "")
    observed, limits = get("observed"), get("limit")
    both = bool(observed) and bool(limits)
    parts: list[str] = []
    # Limits first reads naturally ("requirement … ; observed …") and keeps cues before values.
    for c, v in limits:
        parts.append(f"{_label(c.header)} {_with_unit(v, unit)}" if both or len(limits) > 1 else _with_unit(v, unit))
    for c, v in observed:
        parts.append(f"{_label(c.header)} {_with_unit(v, unit)}" if both or len(observed) > 1 else _with_unit(v, unit))
    for _, v in get("other"):
        parts.append(_with_unit(v, unit))
    for _, v in get("verdict"):
        parts.append(v)
    qty = next((v for _, v in get("qty")), None)
    tail = f" (quantity {qty}{(' ' + unit.rstrip('.')) if unit and not NUMERIC.match(unit) else ''})" if qty else ""
    if not parts:
        return f"{name.rstrip('.')}{tail}."
    return f"{name}: {'; '.join(p.rstrip('.') for p in parts)}{tail}."


def linearize_tables(text: str) -> str:
    """Rewrite each pipe table in ``text`` as one statement per data row (same line count)."""
    lines = text.split("\n")
    out = list(lines)
    i = 0
    while i < len(lines):
        if not PIPE_ROW.match(lines[i]):
            i += 1
            continue
        j = i
        while j < len(lines) and PIPE_ROW.match(lines[j]):
            j += 1
        block = [_cells(l) for l in lines[i:j]]
        width = max(len(r) for r in block)
        block = [r + [""] * (width - len(r)) for r in block]
        if _is_header(block[0]):
            header, rows, first = block[0], block[1:], i + 1
            out[i] = ""
        else:
            header, rows, first = [""] * width, block, i
        cols = _roles(header, rows)
        for k, cells in enumerate(rows):
            text_row = _row_text(cols, cells)
            out[first + k] = text_row if text_row else lines[first + k]
        i = j
    return "\n".join(out)
