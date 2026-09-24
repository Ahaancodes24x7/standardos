"""Compose realistic tender documents and their gold labels from the clause bank.

A document = NIT header (with Hindi) → instructions to bidders → commercial
conditions → scope → site conditions → one technical section per trade (with
guaranteed technical particulars) → tests and inspection → documentation and
warranty → schedule of quantities → approved makes → notes and signature block.

Only clauses from the clause bank are requirements; every other line is the
kind of text a real tender contains and a requirement extractor must ignore.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .clauses import DOMAINS, GENERIC, PACKAGES, VAGUE, Domain, Plant, T

# Per-unit surface forms: (dev pool, extra forms only the test split may use).
FORMS: dict[str, tuple[list[str], list[str]]] = {
    "V": (["{n} V", "{n}V", "{n} volts"], ["{n} Volts", "{n} Volt"]),
    "kV": (["{n} kV", "{n}kV"], ["{n} KV", "{n} K.V."]),
    "A": (["{n} A", "{n}A"], ["{n} Amps", "{n} Amp"]),
    "kA": (["{n} kA", "{n}kA"], ["{n} KA", "{n} k.A."]),
    "degC": (["{n} °C", "{n}°C", "{n} deg C"], ["{n} Deg.C", "{n} degree centigrade"]),
    "mm2": (["{n} sq mm", "{n} sq.mm", "{n} mm²"], ["{n} Sq.mm", "{n} sqmm"]),
    "kW": (["{n} kW", "{n}kW"], ["{n} KW", "{n} Kw"]),
    "Hz": (["{n} Hz", "{n}Hz"], ["{n} c/s", "{n} HZ"]),
    "m3h": (["{n} m3/hr", "{n} m³/h"], ["{n} cum/hr", "{n} m3/h"]),
    "mgl": (["{n} mg/l", "{n} mg/L"], ["{n} ppm", "{n} mg/litre"]),
    "ohm": (["{n} ohm", "{n} ohms"], ["{n} Ω", "{n} Ohm"]),
    "mm": (["{n} mm", "{n}mm"], ["{n} mm.", "{n} MM"]),
    "m": (["{n} m", "{n} metres"], ["{n} mtrs", "{n} M"]),
    "pct": (["{n} %", "{n}%"], ["{n} percent", "{n} per cent"]),
    "kVA": (["{n} kVA", "{n}kVA"], ["{n} KVA", "{n} K.V.A."]),
    "rpm": (["{n} rpm", "{n} RPM"], ["{n} r.p.m."]),
    "NTU": (["{n} NTU"], ["{n} N.T.U."]),
    "dBA": (["{n} dB(A)", "{n} dBA"], ["{n} db(A)"]),
    "kgm3": (["{n} kg/m3", "{n} kg/m³"], ["{n} kg/cum", "{n} Kg/cum"]),
    "days": (["{n} days"], ["{n} days"]),
}
TOKEN = re.compile(r"\{\{([^|}]+)\|([^}]+)\}\}")

HINDI = ["निविदा आमंत्रण सूचना", "तकनीकी विशिष्टियाँ", "कार्यपालक अभियंता", "लोक निर्माण विभाग"]

ITB = [
    "The bidder shall submit the EMD in the form of online payment or bank guarantee from a scheduled bank.",
    "The bid shall remain valid for 90 days from the date of opening of the technical bid.",
    "Bidders shall have completed at least one similar work of value not less than 40 % of the estimated cost during the last seven years.",
    "Conditional bids will be summarily rejected.",
    "The tender documents may be downloaded from the e-procurement portal of the Government.",
    "The bidder must be registered with the Department in the appropriate class.",
    "The Department reserves the right to accept or reject any bid without assigning any reason.",
    "The successful bidder shall furnish a performance guarantee of 5 % of the contract value within 15 days.",
    "Bids received after the due date and time shall not be considered.",
    "The bidder shall upload scanned copies of GST registration, PAN and audited balance sheets.",
]
GCC = [
    "Payment shall be made within 30 days of receipt of bills duly certified by the Engineer-in-charge.",
    "Liquidated damages at 0.5 % per week of delay shall be levied, subject to a maximum of 10 % of the contract value.",
    "All disputes shall be subject to arbitration under the Arbitration and Conciliation Act, 1996.",
    "The contractor shall comply with all labour laws and the provisions of the Contract Labour Act.",
    "Income tax and GST shall be deducted at source as applicable.",
    "Rates quoted shall be inclusive of all taxes, freight, insurance and transit risks.",
    "The contractor shall indemnify the Department against all claims arising out of the work.",
]
NOTES = [
    "Note: Drawings are indicative only and shall be verified at site.",
    "Note: In case of any discrepancy between drawings and specifications, the decision of the Engineer-in-charge shall be final.",
    "Note: Quantities are approximate and may vary during execution.",
]
ITB_HEADINGS = ["INSTRUCTIONS TO BIDDERS", "SECTION I — INSTRUCTIONS TO TENDERERS", "PART A — INSTRUCTIONS TO BIDDERS"]
GCC_HEADINGS = ["GENERAL CONDITIONS OF CONTRACT", "COMMERCIAL TERMS AND CONDITIONS", "SPECIAL CONDITIONS OF CONTRACT"]
BOQ_HEADINGS = ["SCHEDULE OF QUANTITIES", "BILL OF QUANTITIES"]
MAKES_HEADINGS = ["LIST OF APPROVED MAKES", "APPROVED MAKES OF MATERIALS"]
NUMBERING = ["decimal", "paren_alpha", "roman", "plain_number", "dash"]


@dataclass
class Clause:
    text: str
    cat: str
    attrs: list[dict[str, Any]]
    std: Optional[str]


@dataclass
class Generated:
    id: str
    split: str
    name: str
    organization: str
    domain: str
    text: str
    requirements: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    plants: list[str] = field(default_factory=list)
    style: dict[str, Any] = field(default_factory=dict)


class Styler:
    """Per-document writing style: unit spellings, numbering, capitals."""

    def __init__(self, rng: random.Random, split: str) -> None:
        self.rng = rng
        pool = {u: (dev + test if split == "test" else dev) for u, (dev, test) in FORMS.items()}
        self.forms = {u: rng.choice(p) for u, p in pool.items()}
        self.numbering = rng.choice(NUMBERING)
        self.caps_rate = rng.choice([0, 0, 0.08])
        self.merge_rate = rng.choice([0, 0.12, 0.2])

    def render(self, text: str) -> str:
        def sub(m: re.Match[str]) -> str:
            n, unit = m.group(1), m.group(2)
            return self.forms[unit].format(n=n)

        return TOKEN.sub(sub, text)

    def number(self, section: int, i: int) -> str:
        return {
            "decimal": f"{section}.{i}",
            "paren_alpha": f"({chr(96 + i)})" if i <= 26 else f"({i})",
            "roman": f"{_roman(i).lower()})",
            "plain_number": f"{i}.",
            "dash": "-",
        }[self.numbering]


def _roman(n: int) -> str:
    vals = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


CITATION = re.compile(r"\b(?:IS|IEC)\b\s*[/:]?\s*(?:IEC\s*)?\d")


def _gold(text: str, c: "Clause") -> dict[str, Any]:
    """Gold requirement. Mapping gold only for requirements that cite no standard (retrieval's job)."""
    gold: dict[str, Any] = {"text": text, "category": c.cat, "attributes": c.attrs}
    if c.std and not CITATION.search(text):
        gold["standard"] = c.std
    return gold


def _variant(variants: list[str], split: str, rng: random.Random) -> str:
    if split == "dev" or len(variants) == 1:
        return variants[0]
    return rng.choice(variants[1:])


def compose(doc_id: str, split: str, package_index: int, n_plants: int, seed: int) -> Generated:
    rng = random.Random(seed)
    work, domain_ids, org = PACKAGES[package_index % len(PACKAGES)]
    domains: list[Domain] = [DOMAINS[d] for d in domain_ids]
    style = Styler(rng, split)

    # --- choose plants (at most one per template; dependency targets must stay uncited) ---
    candidates: list[Plant] = [p for d in domains for p in d.plants]
    if "lt_panel" in domain_ids or "wiring" in domain_ids:
        candidates += VAGUE
    rng.shuffle(candidates)
    chosen: list[Plant] = []
    used_keys: set[str] = set()
    for p in candidates:
        if len(chosen) >= n_plants:
            break
        keys = {p.replaces or p.key, *p.companions}
        if keys & used_keys:
            continue
        chosen.append(p)
        used_keys |= keys

    by_key: dict[str, Plant] = {p.replaces: p for p in chosen if p.replaces}
    companion_text: dict[str, list[str]] = {k: v for p in chosen for k, v in p.companions.items()}

    def clause_for(t: T) -> Optional[Clause]:
        plant = by_key.get(t.key)
        if plant is not None:
            if not plant.variants:
                return None
            attrs = plant.attrs or ([] if plant.group == "gap" else t.attrs)
            return Clause(style.render(_variant(plant.variants, split, rng)), plant.cat or t.cat, attrs, plant.std or t.std)
        variants = companion_text.get(t.key, t.variants)
        return Clause(style.render(_variant(variants, split, rng)), t.cat, t.attrs, t.std)

    # --- header ---
    tender_no = f"{rng.choice(['EE', 'SE', 'CE'])}/{rng.choice(['ELE', 'CIV', 'WS', 'MM'])}/{rng.randint(10, 99)}/{2026}-27"
    lines: list[str] = []
    lines.append(org)
    if rng.random() < 0.7:
        lines.append(rng.choice(HINDI))
    lines += [
        f"Office of the Executive Engineer, {rng.choice(['Division No. 2', 'Electrical Division', 'Project Division', 'Circle I'])}",
        f"NOTICE INVITING e-TENDER No. {tender_no}",
        f"Name of work: {work}.",
        f"Estimated cost put to tender: Rs. {rng.randint(18, 480)},{rng.randint(10, 99)},000/-",
        f"Earnest Money Deposit: Rs. {rng.randint(1, 9)},{rng.randint(10, 99)},000/-",
        f"Period of completion: {rng.choice([6, 9, 12, 18])} months",
        f"Last date of submission: {rng.randint(10, 28)}.{rng.randint(10, 12)}.2026 up to 15:00 hrs",
        "",
    ]
    lines += [rng.choice(ITB_HEADINGS)]
    for i, t in enumerate(rng.sample(ITB, rng.randint(4, 7)), 1):
        lines.append(f"{i}. {t}")
    lines.append("")
    if rng.random() < 0.8:
        lines.append(rng.choice(GCC_HEADINGS))
        for i, t in enumerate(rng.sample(GCC, rng.randint(3, 5)), 1):
            lines.append(f"{i}. {t}")
        lines.append("")
    lines += ["SCOPE OF WORK", f"This specification covers {work.lower()} complete in all respects.", ""]

    requirements: list[dict[str, Any]] = []

    def emit(section_no: int, clauses: list[Clause]) -> None:
        i = 0
        pending: Optional[Clause] = None
        for c in clauses:
            text = c.text.upper() if rng.random() < style.caps_rate else c.text
            requirements.append(_gold(text, c))
            if pending is None and rng.random() < style.merge_rate:
                pending = Clause(text, c.cat, c.attrs, c.std)
                continue
            i += 1
            body = f"{pending.text} {text}" if pending else text
            pending = None
            prefix = style.number(section_no, i)
            lines.append(f"{prefix} {body}")
        if pending:
            i += 1
            lines.append(f"{style.number(section_no, i)} {pending.text}")

    section = 3
    site = [c for d in domains for t in d.templates if t.section == "site" for c in [clause_for(t)] if c]
    if site:
        lines.append(f"{section} SITE CONDITIONS" if style.numbering == "decimal" else "SITE CONDITIONS")
        emit(section, site)
        lines.append("")
        section += 1

    tests: list[Clause] = []
    for d in domains:
        spec = [c for t in d.templates if t.section == "spec" for c in [clause_for(t)] if c]
        vague = [p for p in chosen if p.replaces is None and p.variants]
        if d is domains[0]:
            for p in vague:
                spec.insert(rng.randint(0, len(spec)), Clause(style.render(_variant(p.variants, split, rng)), p.cat, [], None))
        heading = rng.choice([f"{section} TECHNICAL SPECIFICATION — {d.heading}", f"SECTION {section}: {d.heading}", f"PART {chr(64 + section)} — {d.heading}"])
        lines.append(heading)
        emit(section, spec)
        lines.append("")
        gtp = [c for t in d.templates if t.section == "gtp" for c in [clause_for(t)] if c]
        if gtp and d.gtp_title:
            lines.append(d.gtp_title)
            for c in gtp:
                requirements.append(_gold(c.text, c))
                lines.append(c.text)
            lines.append("Make and type: (to be furnished by the bidder)")
            lines.append("")
        tests += [c for t in d.templates if t.section == "tests" for c in [clause_for(t)] if c]
        section += 1

    tests += [c for t in GENERIC if t.section == "tests" for c in [clause_for(t)] if c]
    lines.append(rng.choice([f"{section} TESTS AND INSPECTION", f"SECTION {section}: TESTING, INSPECTION AND CERTIFICATION"]))
    emit(section, tests)
    lines.append("")
    section += 1
    docs = [c for d in domains for t in d.templates if t.section == "docs" for c in [clause_for(t)] if c]
    docs += [c for t in GENERIC if t.section == "docs" for c in [clause_for(t)] if c]
    lines.append(f"{section} DOCUMENTATION, WARRANTY AND TRAINING")
    emit(section, docs)
    lines.append("")

    lines += [rng.choice(BOQ_HEADINGS), "Sl. No. | Description | Unit | Qty"]
    for i, row in enumerate([r for d in domains for r in d.boq], 1):
        lines.append(f"{i} | {row}")
    lines += ["", rng.choice(MAKES_HEADINGS)]
    for d in domains:
        lines.append(d.makes)
    lines.append("")
    lines += rng.sample(NOTES, 2)
    lines += ["", "Signature of Bidder with seal", "Executive Engineer"]
    text = "\n".join(lines) + "\n"

    # --- gold findings: plants + automatic amendment reminders (once per standard) ---
    findings = [dict(p.gold) for p in chosen]
    all_req_text = "\n".join(r["text"] for r in requirements)
    for pattern, sid in ((r"\bIS\s*456\b", "is-456-2000"), (r"\bIS\s*10500\b", "is-10500-2012")):
        if re.search(pattern, all_req_text, re.I):
            findings.append({"group": "outdated", "standardId": sid, "why": "amendments to confirm"})
    # A dependency plant is only valid if nothing else cites its target.
    valid = []
    from standardos_aiml.standards.seed import seed_corpus

    corpus = seed_corpus()
    for f in findings:
        if f["group"] == "dependency":
            target = corpus.standard(f["standardId"])
            designation = target.designation if target else ""
            if designation and re.search(re.escape(designation) + r"(?![\d-])", all_req_text):
                continue
        valid.append(f)

    return Generated(
        id=doc_id,
        split=split,
        name=f"{work} — {tender_no}",
        organization=org,
        domain=", ".join(d.title for d in domains),
        text=text,
        requirements=requirements,
        findings=valid,
        plants=[p.key for p in chosen],
        style={"units": style.forms, "numbering": style.numbering, "caps_rate": style.caps_rate, "merge_rate": style.merge_rate},
    )


def queries(split: str) -> list[dict[str, Any]]:
    """Isolated retrieval queries from templates marked ``query`` (dev: variant 0; test: variant 1)."""
    out = []
    for d in DOMAINS.values():
        for t in d.templates:
            if not t.query or not t.std:
                continue
            idx = 0 if split == "dev" else min(1, len(t.variants) - 1)
            text = TOKEN.sub(lambda m: f"{m.group(1)} {_canonical_unit(m.group(2))}", t.variants[idx])
            out.append(
                {"id": f"rw2-{split}-{t.key}", "split": split, "text": text, "standards": {t.std: 2}, "clauses": list(t.clauses)}
            )
    return out


def _canonical_unit(unit: str) -> str:
    return {"degC": "°C", "mm2": "sq mm", "m3h": "m3/hr", "mgl": "mg/l", "pct": "%", "kgm3": "kg/m3", "dBA": "dB(A)"}.get(unit, unit)
