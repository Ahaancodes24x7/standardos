# StandardOS benchmark — standardos-pipeline/2.0.0-py

Corpus `seed-6ada30cf` · generated 2026-09-23T10:32:11+00:00

6 tender-realistic specifications (176 gold requirements, 25 gold findings) in three formats, plus 50 retrieval queries. Gold labels were written before the system was run on these documents, and no engine code or weights were changed after scoring. See `benchmark/README.md` for how the set was built and its limits.

## Headline (TXT input)

| Task | Metric | Value |
| --- | --- | --- |
| Requirement identification | P / R / F1 | 92.9% / 96.0% / 94.4% |
| Requirement classification | accuracy / macro-F1 | 69.2% / 67.6% |
| Attribute extraction | P / R / F1 | 95.3% / 96.2% / 95.8% |
| Compliance findings | P / R / F1 | 65.7% / 92.0% / 76.7% |
| Standard retrieval (bm25+rerank) | R@1 / R@3 / MRR | 88.0% / 98.0% / 0.930 |
| Clause retrieval (bm25+rerank) | R@1 / R@3 | 86.0% / 92.0% |
| Latency | mean per specification | 49.1 ms |

## By input format

| Format | Identification P / R / F1 | Classification acc. | Attribute F1 | Findings P / R / F1 | Mean latency |
| --- | --- | --- | --- | --- | --- |
| TXT | 92.9% / 96.0% / 94.4% | 69.2% | 95.8% | 65.7% / 92.0% / 76.7% | 49.1 ms |
| PDF | 91.8% / 96.0% / 93.9% | 68.6% | 94.8% | 64.7% / 88.0% / 74.6% | 138.1 ms |
| DOCX | 92.9% / 96.6% / 94.7% | 69.4% | 96.7% | 65.7% / 92.0% / 76.7% | 72.2 ms |

## Compliance findings by detector (TXT)

| Detector | Precision | Recall | F1 | TP/FP/FN |
| --- | --- | --- | --- | --- |
| conflict | 80.0% | 100.0% | 88.9% | 8/2/0 |
| gap | 33.3% | 75.0% | 46.2% | 3/6/1 |
| dependency | 60.0% | 75.0% | 66.7% | 3/2/1 |
| outdated | 88.9% | 100.0% | 94.1% | 8/1/0 |
| certification | 50.0% | 100.0% | 66.7% | 1/1/0 |

## Per document (TXT)

| Doc | Domain | Req P / R | Findings TP/FP/FN | Readiness | Findings raised (non-verified) | Repairs |
| --- | --- | --- | --- | --- | --- | --- |
| b1 | electrical — LV switchgear, protective devices, cables, earthing | 88.1% / 92.5% | 4/1/1 | 77 | 5 | 4 |
| b2 | water supply — submersible pumpsets, cables, starters, drinking-water quality | 88.9% / 100.0% | 4/4/0 | 80 | 8 | 7 |
| b3 | civil — reinforced concrete, water-retaining structure, severe exposure | 100.0% / 100.0% | 4/1/0 | 79 | 5 | 3 |
| b4 | power distribution — transformers, MV cables, LV circuit breakers | 85.2% / 88.5% | 4/2/1 | 58 | 6 | 6 |
| b5 | water supply — horizontal centrifugal pumps, induction motors | 100.0% / 96.6% | 0/2/0 | 91 | 2 | 2 |
| b6 | building services — wiring, distribution boards, protection, earthing | 100.0% / 100.0% | 7/2/0 | 65 | 9 | 9 |

## Retrieval ablation (50 queries)

| Configuration | Std R@1 | Std R@3 | Std MRR | nDCG@5 | Clause R@1 | Clause R@3 | Clause MRR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bm25 | 92.0% | 98.0% | 0.950 | 0.951 | 80.0% | 96.0% | 0.884 |
| bm25+thesaurus | 90.0% | 98.0% | 0.940 | 0.945 | 80.0% | 94.0% | 0.876 |
| bm25+rerank | 88.0% | 98.0% | 0.930 | 0.931 | 86.0% | 92.0% | 0.893 |
| bm25+thesaurus+rerank | 88.0% | 98.0% | 0.930 | 0.926 | 86.0% | 92.0% | 0.893 |

## Classification F1 by category (TXT)

| Category | F1 |
| --- | --- |
| performance | 95.2% |
| quality | 90.9% |
| environmental | 83.3% |
| certification | 83.3% |
| testing | 78.8% |
| documentation | 70.6% |
| material | 70.0% |
| electrical | 69.8% |
| safety | 63.6% |
| dimensional | 62.5% |
| general | 43.5% |
| installation | 0.0% |

## Error listing (TXT)

### b1 — LT electrical distribution system — CPWD NIT 14/EE(E)/EED/2026-27

**Missed requirements:**
- The area falls under seismic zone III.
- Rated short-time withstand current: 50 kA for 1 s
- Form of separation: Form 3b

**Spurious requirements:**
- Last date and time of bid submission: 18.11.2026 up to 15:00 hrs
- The bidder shall submit the EMD in the form of an online payment or bank guarantee from a scheduled bank.
- The bid shall remain valid for 90 days from the date of opening of the technical bid.
- Bidders shall have completed at least one similar work of value not less than Rs. 1.47 crore during the last seven years.
- | 3.5C x 300 sq mm XLPE armoured cable | m | 480

**Missed findings:**
- dependency is-10810  — IS 7098 (Part 1) cables are tested per IS 10810; the specification only asks for an IR test.

**Unexpected findings:**
- gap [insufficient_specification] Design and routine verification is not measurable (is-iec-61439-1-2020)

**Classification errors (gold → predicted):** electrical → general, electrical → general, safety → electrical, electrical → material, installation → electrical, installation → material, safety → general, safety → general, general → installation

### b2 — Borewell submersible pumpsets and water quality — PHED/JJM NIT 23/2026-27

**Spurious requirements:**
- The bidder must be registered with the Department in the appropriate class.
- Rates quoted shall be inclusive of all taxes, freight, insurance and transit risks.
- | Submersible pumpset 11 kW, 18 m3/h at 90 m | No. | 34
- | 3C x 10 sq mm submersible flat cable | m | 3400

**Unexpected findings:**
- gap [checklist_gap] Efficiency class is unspecified (is-325-1996)
- dependency [dependency_gap] Test method IS 4029:2010 is not specified (is-4029-2010)
- dependency [dependency_gap] IS/IEC 61439-2 depends on IS/IEC 61439-1, which is not addressed (is-iec-61439-1-2020)
- gap [vague_requirement] Requirement is not measurable (is-12615-2018)

**Classification errors (gold → predicted):** electrical → material, installation → testing, electrical → environmental, safety → electrical, installation → environmental, quality → general, documentation → certification, general → installation, general → installation

### b3 — 500 KL RCC elevated storage reservoir, coastal — TWAD Board 07/2026

**Unexpected findings:**
- outdated [amendment_check] Amendments to IS 456:2000 should be confirmed (is-456-2000)

**Classification errors (gold → predicted):** environmental → dimensional, material → general, material → general, installation → general, installation → general, installation → general, performance → dimensional, general → testing, general → material, material → general, documentation → testing

### b4 — 630 kVA distribution transformers, 11 kV cables and LT breakers — MVVNL enquiry 41/2026-27

**Missed requirements:**
- Type: Outdoor, three phase, oil immersed, naturally cooled (ONAN), copper wound.
- Cooling: ONAN
- Energy efficiency level: Level 2

**Spurious requirements:**
- Subject: Procurement of 630 kVA, 11/0.433 kV distribution transformers, 11 kV cables and LT circuit breakers under the RDSS scheme.
- Sealed bids are invited from manufacturers having valid BIS licence for distribution transformers.
- The bidder shall have supplied at least 500 transformers of 630 kVA or higher rating to any State utility during the last five years.
- SECTION IV – 11 kV POWER CABLES

**Missed findings:**
- gap   — 'No-load losses shall be as low as possible' is not measurable.

**Unexpected findings:**
- conflict [constraint_conflict] Potential ambient temperature conflict (is-iec-61439-1-2020)
- conflict [constraint_conflict] Potential rated voltage conflict (is-7098-1-1988)

**Classification errors (gold → predicted):** general → electrical, documentation → material, electrical → material, general → dimensional, documentation → electrical, general → electrical

### b5 — Raw water pumping machinery, Kanher Dam — MJP Satara E-12/2026-27

**Missed requirements:**
- Type: Horizontal split casing, single stage, double suction

**Unexpected findings:**
- gap [checklist_gap] Conductor cross-section is unspecified (is-7098-1-1988)
- gap [vague_requirement] Requirement is not measurable (is-325-1996)

**Classification errors (gold → predicted):** environmental → dimensional, electrical → performance, electrical → general, testing → installation, electrical → material, general → testing, general → testing

### b6 — Internal electrification, girls' hostel — Karnataka PWD STN 09/2026-27

**Unexpected findings:**
- gap [vague_requirement] Requirement is not measurable (is-694-2010)
- certification [conformity_evidence_missing] Conformity evidence is not specified for 3 product standards (is-694-2010)

**Classification errors (gold → predicted):** general → certification, general → documentation, installation → material, electrical → material, dimensional → electrical, safety → electrical, general → dimensional, safety → electrical, safety → general, testing → safety

### Retrieval misses (bm25+rerank)

- bq4: expected is-iec-61439-1-2020, got is-3043-2018, is-iec-61439-1-2020, is-iec-60947-2-2003
- bq10: expected is-12640-1-2016|is-732-2019, got is-iec-60898-1-2002, is-12640-1-2016, is-iec-60947-2-2003
- bq20: expected is-3043-2018, got is-732-2019, is-3043-2018, is-12640-1-2016
- bq28: expected is-2026-1-2011, got is-iec-61439-1-2020, is-325-1996, is-4029-2010
- bq40: expected is-516-1-1-2021, got is-456-2000, is-516-1-1-2021, is-516-1959
- bq47: expected is-3025, got is-10500-2012, is-3025, is-14543-2016
