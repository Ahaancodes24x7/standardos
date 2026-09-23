"""Entity resolution for standard designations.

Tender documents cite the same standard many ways ("IS:1554-1",
"IS 1554 (Pt 1):1988", "IEC 61439-1"), so references are normalised to a
canonical designation and matched in order of decreasing certainty:

1. exact designation or alias             (confidence 0.98)
2. IEC/ISO number → adopted IS/IEC record  (0.9)
3. family fallback: drop section, then part (0.7 / 0.6)
4. cited without a part: the only part (0.8) or Part 1 (0.6)

Unresolved references are returned with ``standard_id = None`` so the UI can
show them as "not in the corpus" rather than guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from ..provenance import provenance
from ..types import Corpus, CorpusStandard, Provenance, StandardReference


@dataclass
class ResolvedReference:
    reference: StandardReference
    standard_id: Optional[str]
    edition: str  # current | older | newer | unspecified | unknown
    replaced_by_id: Optional[str]
    provenance: Provenance


def designation_key(designation: str) -> str:
    key = designation.upper().replace("PART", "PT")
    key = re.sub(r"SECTION|SEC\.?", "SEC", key)
    return re.sub(r"[^A-Z0-9/]", "", key)


def _first_number(designation: str) -> Optional[str]:
    m = re.search(r"(\d{2,5})", designation)
    return m.group(1) if m else None


class StandardResolver:
    def __init__(self, corpus: Corpus) -> None:
        self.corpus = corpus
        self._by_key: dict[str, list[CorpusStandard]] = {}
        self._by_number: dict[str, list[CorpusStandard]] = {}
        for std in corpus.standards:
            for name in [std.designation, *std.aliases]:
                self._add(self._by_key, designation_key(name), std)
            num = _first_number(std.designation)
            if num:
                self._add(self._by_number, num, std)

    @staticmethod
    def _add(index: dict[str, list[CorpusStandard]], key: str, std: CorpusStandard) -> None:
        bucket = index.setdefault(key, [])
        if std not in bucket:
            bucket.append(std)

    def get(self, standard_id: str) -> Optional[CorpusStandard]:
        return self.corpus.standard(standard_id)

    @staticmethod
    def _pick(candidates: list[CorpusStandard], year: Optional[int]) -> Optional[CorpusStandard]:
        """Among records sharing a designation, prefer the cited year, else the current one."""
        if year is not None:
            exact = next((s for s in candidates if s.year == year), None)
            if exact:
                return exact
        current = next((s for s in candidates if s.status not in ("superseded", "withdrawn")), None)
        return current or (candidates[0] if candidates else None)

    def resolve(self, reference: StandardReference) -> ResolvedReference:
        key = designation_key(reference.designation)
        signals = [f'normalised "{reference.raw}" → {reference.designation}']
        std: Optional[CorpusStandard] = None
        confidence = 0.0

        exact = self._by_key.get(key)
        if exact:
            std = self._pick(exact, reference.year)
            confidence = 0.98
            signals.append("exact designation match")
        if not std and re.match(r"(IEC|ISO)", reference.designation):
            adopted = self._by_key.get(designation_key(f"IS/{reference.designation}"))
            if adopted:
                std = self._pick(adopted, None)
                confidence = 0.9
                signals.append("matched the Indian adoption (IS/IEC) of the cited IEC/ISO standard")
        if not std:
            # Family fallback: "IS 3025 (Part 11)" → the IS 3025 series record,
            # "IS 516 (Part 1/Sec 1)" → IS 516 (Part 1) → IS 516.
            without_sec = re.sub(r"/Sec \d+\)", ")", reference.designation, count=1)
            without_part = re.sub(r"\s*\(Part [^)]+\)|-\d+$", "", reference.designation, count=1)
            for candidate, conf, why in (
                (without_sec, 0.7, "matched after dropping the section number"),
                (without_part, 0.6, "matched the standard family after dropping the part number"),
            ):
                if candidate == reference.designation:
                    continue
                found = self._by_key.get(designation_key(candidate))
                if found:
                    std = self._pick(found, reference.year)
                    confidence = conf
                    signals.append(why)
                    break

        if not std and not re.search(r"\(Part|-\d+$", reference.designation):
            # Cited without a part number ("IS 8623:1993") while the corpus holds
            # parts: take the only part, or Part 1 (general rules) when several exist.
            num = _first_number(reference.designation) or ""
            is_iec = "/" in reference.designation
            family = [s for s in self._by_number.get(num, []) if ("/" in s.designation) == is_iec]
            parts = list(dict.fromkeys(s.designation for s in family))
            chosen = (
                parts[0]
                if len(parts) == 1
                else next((d for d in parts if re.search(r"\(Part 1\)|-1$", d)), None)
            )
            if chosen:
                std = self._pick([s for s in family if s.designation == chosen], reference.year)
                confidence = 0.8 if len(parts) == 1 else 0.6
                signals.append(
                    f"cited without a part number; the corpus holds only {chosen}"
                    if len(parts) == 1
                    else f"cited without a part number; assumed {chosen} (general part)"
                )

        if not std:
            signals.append("no corpus record for this designation")
            return ResolvedReference(reference, None, "unknown", None, provenance("standards.resolve", "rule", 0, signals))

        edition = "unspecified"
        replaced_by_id: Optional[str] = None
        if reference.year is not None:
            if reference.year == std.year:
                edition = "current"
            elif reference.year < std.year:
                edition = "older"
                prior = next(
                    (
                        p
                        for p in self.corpus.prior_editions
                        if designation_key(p.designation) == designation_key(std.designation) and p.year == reference.year
                    ),
                    None,
                )
                replaced_by_id = prior.replaced_by_id if prior else std.id
                signals.append(f"cited edition {reference.year} is older than the {std.year} edition in the corpus")
            else:
                edition = "newer"
                signals.append(
                    f"cited edition {reference.year} is newer than the corpus record ({std.year}); corpus may be out of date"
                )
        return ResolvedReference(
            reference, std.id, edition, replaced_by_id, provenance("standards.resolve", "rule", confidence, signals)
        )
