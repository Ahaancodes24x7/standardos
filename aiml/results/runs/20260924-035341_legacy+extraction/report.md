# Evaluation run `20260924-035341_legacy+extraction`

Config **legacy+extraction** · pipeline `standardos-pipeline/3.0.0-py` · corpus `seed-6ada30cf` · commit `35d8bc5` · 2026-09-24T03:53:41+00:00 · 19.5 s

Percentages with a 95% bootstrap CI (resampling documents/queries) in brackets. Split roles: **open** = used in development; **contaminated** = inspected during changes (report only); **blind** = frozen, scored only on request.

> pipeline 3.0.0 official (legacy+extraction)

## Documents: extraction, classification, mapping, findings

| Dataset / split / format | Role | n | Req. ident. F1 | Ident. P | Ident. R | Class. acc. | Class. macro-F1 | Attr. F1 | Mapping acc. | Findings P | Findings R | Findings F1 | ms/doc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| component / dev / txt | open | 8 | 92.0 <sub>[74–100]</sub> | 100.0 | 85.2 <sub>[59–100]</sub> | 82.6 <sub>[63–100]</sub> | 71.1 <sub>[48–100]</sub> | 97.0 <sub>[94–100]</sub> | — | 100.0 | 100.0 | 100.0 | 8 |
| component / test / txt | contaminated | 8 | 97.8 <sub>[93–100]</sub> | 95.7 <sub>[87–100]</sub> | 100.0 | 68.2 <sub>[47–84]</sub> | 56.3 <sub>[32–75]</sub> | 94.1 <sub>[85–100]</sub> | — | 100.0 | 100.0 | 100.0 | 6 |
| component / heldout / txt | blind | 5 | 100.0 | 100.0 | 100.0 | 91.7 <sub>[0–100]</sub> | 85.0 <sub>[0–100]</sub> | 100.0 | — | 100.0 | 87.5 <sub>[50–100]</sub> | 93.3 <sub>[67–100]</sub> | 6 |
| tenders_v1 / all / txt | contaminated | 6 | 97.7 <sub>[95–100]</sub> | 98.8 <sub>[96–100]</sub> | 96.6 <sub>[93–99]</sub> | 69.4 <sub>[62–75]</sub> | 67.7 <sub>[58–72]</sub> | 97.2 <sub>[93–100]</sub> | — | 71.9 <sub>[55–87]</sub> | 92.0 <sub>[83–100]</sub> | 80.7 <sub>[69–89]</sub> | 56 |
| tenders_v1 / all / pdf | contaminated | 6 | 97.1 <sub>[94–99]</sub> | 97.7 <sub>[95–99]</sub> | 96.6 <sub>[93–99]</sub> | 68.8 <sub>[62–74]</sub> | 67.4 <sub>[58–71]</sub> | 96.3 <sub>[92–100]</sub> | — | 71.0 <sub>[53–86]</sub> | 88.0 <sub>[71–100]</sub> | 78.6 <sub>[64–89]</sub> | 118 |
| tenders_v1 / all / docx | contaminated | 6 | 97.7 <sub>[95–100]</sub> | 98.8 <sub>[96–100]</sub> | 96.6 <sub>[93–99]</sub> | 69.4 <sub>[62–75]</sub> | 67.7 <sub>[58–72]</sub> | 97.2 <sub>[93–100]</sub> | — | 71.9 <sub>[55–87]</sub> | 92.0 <sub>[83–100]</sub> | 80.7 <sub>[69–89]</sub> | 88 |
| realworld_v2 / dev / txt | open | 12 | 99.9 <sub>[100–100]</sub> | 100.0 | 99.7 <sub>[99–100]</sub> | 64.6 <sub>[60–69]</sub> | 63.9 <sub>[58–67]</sub> | 96.6 <sub>[95–98]</sub> | 92.7 <sub>[88–97]</sub> | 85.2 <sub>[72–100]</sub> | 82.1 <sub>[67–97]</sub> | 83.6 <sub>[75–93]</sub> | 71 |
| realworld_v2 / dev / pdf | open | 12 | 99.6 <sub>[99–100]</sub> | 99.4 <sub>[98–100]</sub> | 99.7 <sub>[99–100]</sub> | 64.9 <sub>[60–70]</sub> | 64.1 <sub>[58–67]</sub> | 95.2 <sub>[93–98]</sub> | 92.7 <sub>[88–97]</sub> | 78.6 <sub>[67–89]</sub> | 78.6 <sub>[59–97]</sub> | 78.6 <sub>[67–89]</sub> | 96 |
| realworld_v2 / dev / docx | open | 12 | 99.9 <sub>[100–100]</sub> | 100.0 | 99.7 <sub>[99–100]</sub> | 64.6 <sub>[60–69]</sub> | 63.9 <sub>[58–67]</sub> | 96.6 <sub>[95–98]</sub> | 92.7 <sub>[88–97]</sub> | 85.2 <sub>[72–100]</sub> | 82.1 <sub>[67–97]</sub> | 83.6 <sub>[75–93]</sub> | 85 |
| realworld_v2 / test / txt | blind | 18 | 98.9 <sub>[98–100]</sub> | 100.0 | 97.9 <sub>[97–99]</sub> | 70.5 <sub>[66–75]</sub> | 71.5 <sub>[67–75]</sub> | 79.8 <sub>[75–85]</sub> | 93.0 <sub>[90–96]</sub> | 43.8 <sub>[32–56]</sub> | 74.5 <sub>[60–88]</sub> | 55.1 <sub>[43–67]</sub> | 84 |
| realworld_v2 / test / pdf | blind | 18 | 98.8 <sub>[98–99]</sub> | 99.6 <sub>[99–100]</sub> | 97.9 <sub>[97–99]</sub> | 70.7 <sub>[66–75]</sub> | 71.6 <sub>[67–76]</sub> | 79.6 <sub>[75–85]</sub> | 90.9 <sub>[86–95]</sub> | 40.7 <sub>[29–52]</sub> | 74.5 <sub>[60–88]</sub> | 52.6 <sub>[41–64]</sub> | 100 |
| realworld_v2 / test / docx | blind | 18 | 98.9 <sub>[98–100]</sub> | 100.0 | 97.9 <sub>[97–99]</sub> | 70.5 <sub>[66–75]</sub> | 71.5 <sub>[67–75]</sub> | 79.8 <sub>[75–85]</sub> | 93.0 <sub>[90–96]</sub> | 43.8 <sub>[32–56]</sub> | 74.5 <sub>[60–88]</sub> | 55.1 <sub>[43–67]</sub> | 83 |

### Findings F1 by detector

| Dataset / split / format | conflict | gap | dependency | outdated | certification |
| --- | --- | --- | --- | --- | --- |
| component / dev / txt | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| component / test / txt | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| component / heldout / txt | 100.0 | 100.0 | 66.7 | 100.0 | 100.0 |
| tenders_v1 / all / txt | 88.9 | 54.5 | 66.7 | 94.1 | 100.0 |
| tenders_v1 / all / pdf | 88.9 | 54.5 | 66.7 | 87.5 | 100.0 |
| tenders_v1 / all / docx | 88.9 | 54.5 | 66.7 | 94.1 | 100.0 |
| realworld_v2 / dev / txt | 100.0 | 71.4 | 100.0 | 84.2 | 0.0 |
| realworld_v2 / dev / pdf | 100.0 | 58.8 | 100.0 | 82.3 | 0.0 |
| realworld_v2 / dev / docx | 100.0 | 71.4 | 100.0 | 84.2 | 0.0 |
| realworld_v2 / test / txt | 80.0 | 24.6 | 66.7 | 100.0 | 46.2 |
| realworld_v2 / test / pdf | 80.0 | 23.7 | 66.7 | 87.5 | 46.2 |
| realworld_v2 / test / docx | 80.0 | 24.6 | 66.7 | 100.0 | 46.2 |

## Retrieval (isolated requirement sentences)

| Dataset / split | Configuration | n | Std R@1 | Std R@3 | Std MRR | nDCG@5 | Clause R@1 | Clause R@3 | Clause MRR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| component / dev | bm25 | 25 | 100.0 | 100.0 | 1.000 | 0.978 <sub>[0.96–0.99]</sub> | 88.0 <sub>[76–100]</sub> | 100.0 | 0.940 <sub>[0.88–1.00]</sub> |
| component / dev | bm25+thesaurus | 25 | 96.0 <sub>[88–100]</sub> | 100.0 | 0.980 <sub>[0.94–1.00]</sub> | 0.965 <sub>[0.93–0.99]</sub> | 84.0 <sub>[68–96]</sub> | 100.0 | 0.913 <sub>[0.83–0.98]</sub> |
| component / dev | bm25+rerank | 25 | 96.0 <sub>[88–100]</sub> | 100.0 | 0.980 <sub>[0.94–1.00]</sub> | 0.968 <sub>[0.94–0.99]</sub> | 96.0 <sub>[88–100]</sub> | 96.0 <sub>[88–100]</sub> | 0.960 <sub>[0.88–1.00]</sub> |
| component / dev | bm25+thesaurus+rerank | 25 | 96.0 <sub>[88–100]</sub> | 100.0 | 0.980 <sub>[0.94–1.00]</sub> | 0.968 <sub>[0.94–0.99]</sub> | 96.0 <sub>[88–100]</sub> | 96.0 <sub>[88–100]</sub> | 0.960 <sub>[0.88–1.00]</sub> |
| component / test | bm25 | 25 | 96.0 <sub>[88–100]</sub> | 100.0 | 0.980 <sub>[0.94–1.00]</sub> | 0.990 <sub>[0.97–1.00]</sub> | 96.0 <sub>[88–100]</sub> | 100.0 | 0.980 <sub>[0.94–1.00]</sub> |
| component / test | bm25+thesaurus | 25 | 92.0 <sub>[80–100]</sub> | 100.0 | 0.960 <sub>[0.90–1.00]</sub> | 0.977 <sub>[0.94–1.00]</sub> | 92.0 <sub>[80–100]</sub> | 100.0 | 0.960 <sub>[0.90–1.00]</sub> |
| component / test | bm25+rerank | 25 | 96.0 <sub>[88–100]</sub> | 100.0 | 0.980 <sub>[0.94–1.00]</sub> | 0.971 <sub>[0.93–1.00]</sub> | 100.0 | 100.0 | 1.000 |
| component / test | bm25+thesaurus+rerank | 25 | 96.0 <sub>[88–100]</sub> | 100.0 | 0.980 <sub>[0.94–1.00]</sub> | 0.971 <sub>[0.93–1.00]</sub> | 100.0 | 100.0 | 1.000 |
| component / heldout | bm25 | 15 | 100.0 | 100.0 | 1.000 | 0.995 <sub>[0.99–1.00]</sub> | 80.0 <sub>[60–100]</sub> | 86.7 <sub>[67–100]</sub> | 0.863 <sub>[0.71–1.00]</sub> |
| component / heldout | bm25+thesaurus | 15 | 86.7 <sub>[67–100]</sub> | 100.0 | 0.933 <sub>[0.83–1.00]</sub> | 0.964 <sub>[0.93–0.99]</sub> | 66.7 <sub>[40–87]</sub> | 93.3 <sub>[80–100]</sub> | 0.817 <sub>[0.68–0.93]</sub> |
| component / heldout | bm25+rerank | 15 | 93.3 <sub>[80–100]</sub> | 100.0 | 0.956 <sub>[0.87–1.00]</sub> | 0.972 <sub>[0.93–1.00]</sub> | 93.3 <sub>[80–100]</sub> | 100.0 | 0.956 <sub>[0.87–1.00]</sub> |
| component / heldout | bm25+thesaurus+rerank | 15 | 93.3 <sub>[80–100]</sub> | 100.0 | 0.956 <sub>[0.87–1.00]</sub> | 0.967 <sub>[0.92–1.00]</sub> | 93.3 <sub>[80–100]</sub> | 100.0 | 0.956 <sub>[0.87–1.00]</sub> |
| tenders_v1 / all | bm25 | 50 | 92.0 <sub>[84–98]</sub> | 98.0 <sub>[94–100]</sub> | 0.950 <sub>[0.89–0.99]</sub> | 0.951 <sub>[0.90–0.99]</sub> | 80.0 <sub>[68–90]</sub> | 96.0 <sub>[90–100]</sub> | 0.884 <sub>[0.81–0.95]</sub> |
| tenders_v1 / all | bm25+thesaurus | 50 | 90.0 <sub>[80–98]</sub> | 98.0 <sub>[94–100]</sub> | 0.940 <sub>[0.88–0.99]</sub> | 0.945 <sub>[0.89–0.98]</sub> | 80.0 <sub>[68–92]</sub> | 94.0 <sub>[88–100]</sub> | 0.876 <sub>[0.80–0.95]</sub> |
| tenders_v1 / all | bm25+rerank | 50 | 88.0 <sub>[78–96]</sub> | 98.0 <sub>[94–100]</sub> | 0.930 <sub>[0.87–0.98]</sub> | 0.931 <sub>[0.88–0.97]</sub> | 86.0 <sub>[74–94]</sub> | 92.0 <sub>[84–98]</sub> | 0.893 <sub>[0.80–0.96]</sub> |
| tenders_v1 / all | bm25+thesaurus+rerank | 50 | 88.0 <sub>[78–96]</sub> | 98.0 <sub>[94–100]</sub> | 0.930 <sub>[0.87–0.98]</sub> | 0.926 <sub>[0.87–0.97]</sub> | 86.0 <sub>[76–94]</sub> | 92.0 <sub>[84–98]</sub> | 0.893 <sub>[0.81–0.96]</sub> |
| realworld_v2 / dev | bm25 | 35 | 91.4 <sub>[80–100]</sub> | 91.4 <sub>[80–100]</sub> | 0.933 <sub>[0.84–1.00]</sub> | 0.949 <sub>[0.88–1.00]</sub> | 82.9 <sub>[69–94]</sub> | 91.4 <sub>[80–100]</sub> | 0.883 <sub>[0.78–0.96]</sub> |
| realworld_v2 / dev | bm25+thesaurus | 35 | 77.1 <sub>[63–91]</sub> | 94.3 <sub>[86–100]</sub> | 0.862 <sub>[0.78–0.95]</sub> | 0.876 <sub>[0.79–0.95]</sub> | 71.4 <sub>[57–86]</sub> | 94.3 <sub>[86–100]</sub> | 0.817 <sub>[0.72–0.91]</sub> |
| realworld_v2 / dev | bm25+rerank | 35 | 91.4 <sub>[83–100]</sub> | 97.1 <sub>[91–100]</sub> | 0.937 <sub>[0.86–1.00]</sub> | 0.943 <sub>[0.87–1.00]</sub> | 91.4 <sub>[83–100]</sub> | 97.1 <sub>[91–100]</sub> | 0.937 <sub>[0.86–1.00]</sub> |
| realworld_v2 / dev | bm25+thesaurus+rerank | 35 | 82.9 <sub>[71–94]</sub> | 94.3 <sub>[86–100]</sub> | 0.896 <sub>[0.81–0.97]</sub> | 0.913 <sub>[0.83–0.98]</sub> | 82.9 <sub>[71–94]</sub> | 94.3 <sub>[86–100]</sub> | 0.896 <sub>[0.81–0.97]</sub> |
| realworld_v2 / test | bm25 | 35 | 88.6 <sub>[77–97]</sub> | 94.3 <sub>[86–100]</sub> | 0.917 <sub>[0.83–0.99]</sub> | 0.930 <sub>[0.85–0.99]</sub> | 80.0 <sub>[66–91]</sub> | 88.6 <sub>[77–97]</sub> | 0.855 <sub>[0.75–0.95]</sub> |
| realworld_v2 / test | bm25+thesaurus | 35 | 80.0 <sub>[66–91]</sub> | 94.3 <sub>[86–100]</sub> | 0.876 <sub>[0.78–0.96]</sub> | 0.890 <sub>[0.79–0.96]</sub> | 68.6 <sub>[54–83]</sub> | 88.6 <sub>[77–97]</sub> | 0.779 <sub>[0.67–0.89]</sub> |
| realworld_v2 / test | bm25+rerank | 35 | 94.3 <sub>[86–100]</sub> | 97.1 <sub>[91–100]</sub> | 0.960 <sub>[0.90–1.00]</sub> | 0.969 <sub>[0.92–1.00]</sub> | 94.3 <sub>[86–100]</sub> | 97.1 <sub>[91–100]</sub> | 0.960 <sub>[0.90–1.00]</sub> |
| realworld_v2 / test | bm25+thesaurus+rerank | 35 | 91.4 <sub>[83–100]</sub> | 94.3 <sub>[86–100]</sub> | 0.943 <sub>[0.87–1.00]</sub> | 0.957 <sub>[0.90–1.00]</sub> | 91.4 <sub>[83–100]</sub> | 94.3 <sub>[86–100]</sub> | 0.943 <sub>[0.87–1.00]</sub> |

## Resolution, relations, graph construction

| Task | Dataset / split | n | Metrics |
| --- | --- | --- | --- |
| resolution | component / dev | 17 | res_ok 100.0, edition_ok 100.0 |
| relations | component / dev | 20 | rel_precision 100.0, rel_recall 100.0, rel_f1 100.0 |
| resolution | component / test | 17 | res_ok 100.0, edition_ok 100.0 |
| relations | component / test | 18 | rel_precision 100.0, rel_recall 100.0, rel_f1 100.0 |
| resolution | component / heldout | 8 | res_ok 100.0, edition_ok 100.0 |
| relations | component / heldout | 12 | rel_precision 93.8 <sub>[77–100]</sub>, rel_recall 93.8 <sub>[77–100]</sub>, rel_f1 93.8 <sub>[77–100]</sub> |
| graph | corpus / seed-6ada30cf | 18 | edge_precision 78.4 <sub>[60–94]</sub>, edge_recall 80.6 <sub>[62–97]</sub>, edge_f1 79.5 <sub>[61–95]</sub>, pair_f1 98.6 <sub>[95–100]</sub> |

## Configuration

```json
{
  "name": "legacy+extraction",
  "retrieval": {
    "expansion": false,
    "document_context": true,
    "rerank": true,
    "min_confidence": 0.35,
    "top_k": 5
  },
  "zoning": true,
  "heading_v2": true,
  "segmentation_v2": true,
  "attributes_v2": true,
  "lexicon_version": 1,
  "units_v2": false,
  "classifier": "lexicon",
  "rerank_version": 1,
  "product_terms_v2": false,
  "scope_guard": false,
  "dependency_mode": "legacy",
  "detector_gate": false,
  "scoped_checklists": false,
  "vague_version": 1,
  "amendment_dedupe": false,
  "certification_scope": false,
  "relations_version": 1
}
```
