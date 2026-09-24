# Evaluation run `20260924-035011_v3-dag`

Config **v3-dag** · pipeline `standardos-pipeline/3.0.0-py` · corpus `seed-6ada30cf` · commit `35d8bc5` · 2026-09-24T03:50:11+00:00 · 17.4 s

Percentages with a 95% bootstrap CI (resampling documents/queries) in brackets. Split roles: **open** = used in development; **contaminated** = inspected during changes (report only); **blind** = frozen, scored only on request.

## Documents: extraction, classification, mapping, findings

| Dataset / split / format | Role | n | Req. ident. F1 | Ident. P | Ident. R | Class. acc. | Class. macro-F1 | Attr. F1 | Mapping acc. | Findings P | Findings R | Findings F1 | ms/doc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| component / dev / txt | open | 8 | 92.0 <sub>[74–100]</sub> | 100.0 | 85.2 <sub>[59–100]</sub> | 95.7 <sub>[84–100]</sub> | 97.2 <sub>[84–100]</sub> | 97.0 <sub>[94–100]</sub> | — | 90.0 <sub>[86–100]</sub> | 100.0 | 94.7 <sub>[92–100]</sub> | 7 |
| component / test / txt | contaminated | 8 | 97.8 <sub>[93–100]</sub> | 95.7 <sub>[87–100]</sub> | 100.0 | 81.8 <sub>[67–96]</sub> | 76.0 <sub>[57–97]</sub> | 94.1 <sub>[85–100]</sub> | — | 83.3 <sub>[57–100]</sub> | 83.3 <sub>[67–100]</sub> | 83.3 <sub>[70–100]</sub> | 6 |
| component / heldout / txt | blind | 5 | 100.0 | 100.0 | 100.0 | 100.0 <sub>[0–100]</sub> | 100.0 <sub>[0–100]</sub> | 100.0 | — | 100.0 | 100.0 | 100.0 | 5 |
| tenders_v1 / all / txt | contaminated | 6 | 97.7 <sub>[95–100]</sub> | 98.8 <sub>[96–100]</sub> | 96.6 <sub>[93–99]</sub> | 76.5 <sub>[72–80]</sub> | 77.0 <sub>[71–80]</sub> | 97.2 <sub>[93–100]</sub> | — | 73.5 <sub>[58–84]</sub> | 100.0 | 84.8 <sub>[74–92]</sub> | 50 |
| tenders_v1 / all / pdf | contaminated | 6 | 97.1 <sub>[94–99]</sub> | 97.7 <sub>[95–99]</sub> | 96.6 <sub>[93–99]</sub> | 75.9 <sub>[72–79]</sub> | 76.7 <sub>[71–79]</sub> | 96.3 <sub>[92–100]</sub> | — | 72.7 <sub>[58–83]</sub> | 96.0 <sub>[88–100]</sub> | 82.8 <sub>[73–90]</sub> | 86 |
| tenders_v1 / all / docx | contaminated | 6 | 97.7 <sub>[95–100]</sub> | 98.8 <sub>[96–100]</sub> | 96.6 <sub>[93–99]</sub> | 76.5 <sub>[72–80]</sub> | 77.0 <sub>[71–80]</sub> | 97.2 <sub>[93–100]</sub> | — | 73.5 <sub>[58–84]</sub> | 100.0 | 84.8 <sub>[74–92]</sub> | 62 |
| realworld_v2 / dev / txt | open | 12 | 99.9 <sub>[100–100]</sub> | 100.0 | 99.7 <sub>[99–100]</sub> | 78.6 <sub>[76–81]</sub> | 81.7 <sub>[77–84]</sub> | 97.1 <sub>[96–99]</sub> | 96.0 <sub>[94–98]</sub> | 100.0 | 92.9 <sub>[84–100]</sub> | 96.3 <sub>[91–100]</sub> | 52 |
| realworld_v2 / dev / pdf | open | 12 | 99.6 <sub>[99–100]</sub> | 99.4 <sub>[98–100]</sub> | 99.7 <sub>[99–100]</sub> | 78.6 <sub>[76–81]</sub> | 81.8 <sub>[77–84]</sub> | 95.7 <sub>[94–98]</sub> | 96.0 <sub>[94–98]</sub> | 89.3 <sub>[77–100]</sub> | 89.3 <sub>[76–100]</sub> | 89.3 <sub>[80–96]</sub> | 79 |
| realworld_v2 / dev / docx | open | 12 | 99.9 <sub>[100–100]</sub> | 100.0 | 99.7 <sub>[99–100]</sub> | 78.6 <sub>[76–81]</sub> | 81.7 <sub>[77–84]</sub> | 97.1 <sub>[96–99]</sub> | 96.0 <sub>[94–98]</sub> | 100.0 | 92.9 <sub>[84–100]</sub> | 96.3 <sub>[91–100]</sub> | 87 |
| realworld_v2 / test / txt | blind | 18 | 99.1 <sub>[98–100]</sub> | 100.0 | 98.3 <sub>[97–99]</sub> | 80.7 <sub>[78–83]</sub> | 83.1 <sub>[79–86]</sub> | 81.4 <sub>[77–86]</sub> | 92.5 <sub>[88–97]</sub> | 53.8 <sub>[42–66]</sub> | 91.5 <sub>[84–98]</sub> | 67.7 <sub>[57–78]</sub> | 80 |
| realworld_v2 / test / pdf | blind | 18 | 98.9 <sub>[98–100]</sub> | 99.4 <sub>[99–100]</sub> | 98.3 <sub>[97–99]</sub> | 80.8 <sub>[78–84]</sub> | 83.4 <sub>[79–86]</sub> | 81.2 <sub>[77–86]</sub> | 92.5 <sub>[88–97]</sub> | 48.8 <sub>[37–61]</sub> | 89.4 <sub>[80–98]</sub> | 63.2 <sub>[52–74]</sub> | 94 |
| realworld_v2 / test / docx | blind | 18 | 99.1 <sub>[98–100]</sub> | 100.0 | 98.3 <sub>[97–99]</sub> | 80.7 <sub>[78–83]</sub> | 83.1 <sub>[79–86]</sub> | 81.4 <sub>[77–86]</sub> | 92.5 <sub>[88–97]</sub> | 53.8 <sub>[42–66]</sub> | 91.5 <sub>[84–98]</sub> | 67.7 <sub>[57–78]</sub> | 90 |

### Findings F1 by detector

| Dataset / split / format | conflict | gap | dependency | outdated | certification |
| --- | --- | --- | --- | --- | --- |
| component / dev / txt | 100.0 | 100.0 | 80.0 | 100.0 | 100.0 |
| component / test / txt | 100.0 | 0.0 | 100.0 | 100.0 | 100.0 |
| component / heldout / txt | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| tenders_v1 / all / txt | 94.1 | 66.7 | 88.9 | 100.0 | 40.0 |
| tenders_v1 / all / pdf | 94.1 | 66.7 | 88.9 | 93.3 | 40.0 |
| tenders_v1 / all / docx | 94.1 | 66.7 | 88.9 | 100.0 | 40.0 |
| realworld_v2 / dev / txt | 100.0 | 93.3 | 100.0 | 100.0 | 66.7 |
| realworld_v2 / dev / pdf | 100.0 | 77.8 | 100.0 | 93.3 | 66.7 |
| realworld_v2 / dev / docx | 100.0 | 93.3 | 100.0 | 100.0 | 66.7 |
| realworld_v2 / test / txt | 88.9 | 30.2 | 100.0 | 100.0 | 88.9 |
| realworld_v2 / test / pdf | 88.9 | 26.9 | 76.9 | 87.5 | 88.9 |
| realworld_v2 / test / docx | 88.9 | 30.2 | 100.0 | 100.0 | 88.9 |

## Retrieval (isolated requirement sentences)

| Dataset / split | Configuration | n | Std R@1 | Std R@3 | Std MRR | nDCG@5 | Clause R@1 | Clause R@3 | Clause MRR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| component / dev | bm25 | 25 | 100.0 | 100.0 | 1.000 | 0.978 <sub>[0.96–0.99]</sub> | 88.0 <sub>[76–100]</sub> | 100.0 | 0.940 <sub>[0.88–1.00]</sub> |
| component / dev | bm25+thesaurus | 25 | 96.0 <sub>[88–100]</sub> | 100.0 | 0.980 <sub>[0.94–1.00]</sub> | 0.965 <sub>[0.93–0.99]</sub> | 84.0 <sub>[68–96]</sub> | 100.0 | 0.913 <sub>[0.83–0.98]</sub> |
| component / dev | bm25+rerank | 25 | 100.0 | 100.0 | 1.000 | 0.976 <sub>[0.95–0.99]</sub> | 96.0 <sub>[88–100]</sub> | 96.0 <sub>[88–100]</sub> | 0.960 <sub>[0.88–1.00]</sub> |
| component / dev | bm25+thesaurus+rerank | 25 | 100.0 | 100.0 | 1.000 | 0.976 <sub>[0.95–0.99]</sub> | 96.0 <sub>[88–100]</sub> | 96.0 <sub>[88–100]</sub> | 0.960 <sub>[0.88–1.00]</sub> |
| component / test | bm25 | 25 | 96.0 <sub>[88–100]</sub> | 100.0 | 0.980 <sub>[0.94–1.00]</sub> | 0.990 <sub>[0.97–1.00]</sub> | 96.0 <sub>[88–100]</sub> | 100.0 | 0.980 <sub>[0.94–1.00]</sub> |
| component / test | bm25+thesaurus | 25 | 92.0 <sub>[80–100]</sub> | 100.0 | 0.960 <sub>[0.90–1.00]</sub> | 0.977 <sub>[0.94–1.00]</sub> | 92.0 <sub>[80–100]</sub> | 100.0 | 0.960 <sub>[0.90–1.00]</sub> |
| component / test | bm25+rerank | 25 | 100.0 | 100.0 | 1.000 | 0.979 <sub>[0.94–1.00]</sub> | 100.0 | 100.0 | 1.000 |
| component / test | bm25+thesaurus+rerank | 25 | 100.0 | 100.0 | 1.000 | 0.978 <sub>[0.94–1.00]</sub> | 100.0 | 100.0 | 1.000 |
| component / heldout | bm25 | 15 | 93.3 <sub>[80–100]</sub> | 100.0 | 0.967 <sub>[0.90–1.00]</sub> | 0.982 <sub>[0.95–1.00]</sub> | 73.3 <sub>[53–93]</sub> | 86.7 <sub>[67–100]</sub> | 0.830 <sub>[0.68–0.97]</sub> |
| component / heldout | bm25+thesaurus | 15 | 86.7 <sub>[67–100]</sub> | 100.0 | 0.933 <sub>[0.83–1.00]</sub> | 0.964 <sub>[0.93–0.99]</sub> | 66.7 <sub>[40–87]</sub> | 93.3 <sub>[80–100]</sub> | 0.817 <sub>[0.68–0.93]</sub> |
| component / heldout | bm25+rerank | 15 | 93.3 <sub>[80–100]</sub> | 100.0 | 0.956 <sub>[0.87–1.00]</sub> | 0.972 <sub>[0.93–1.00]</sub> | 93.3 <sub>[80–100]</sub> | 100.0 | 0.956 <sub>[0.87–1.00]</sub> |
| component / heldout | bm25+thesaurus+rerank | 15 | 93.3 <sub>[80–100]</sub> | 100.0 | 0.956 <sub>[0.87–1.00]</sub> | 0.967 <sub>[0.92–1.00]</sub> | 93.3 <sub>[80–100]</sub> | 100.0 | 0.956 <sub>[0.87–1.00]</sub> |
| tenders_v1 / all | bm25 | 50 | 92.0 <sub>[84–98]</sub> | 98.0 <sub>[94–100]</sub> | 0.950 <sub>[0.89–0.99]</sub> | 0.954 <sub>[0.91–0.99]</sub> | 80.0 <sub>[68–90]</sub> | 96.0 <sub>[90–100]</sub> | 0.884 <sub>[0.81–0.95]</sub> |
| tenders_v1 / all | bm25+thesaurus | 50 | 92.0 <sub>[84–98]</sub> | 98.0 <sub>[94–100]</sub> | 0.950 <sub>[0.90–0.99]</sub> | 0.954 <sub>[0.91–0.99]</sub> | 82.0 <sub>[70–92]</sub> | 94.0 <sub>[88–100]</sub> | 0.886 <sub>[0.81–0.95]</sub> |
| tenders_v1 / all | bm25+rerank | 50 | 94.0 <sub>[86–100]</sub> | 98.0 <sub>[94–100]</sub> | 0.960 <sub>[0.91–1.00]</sub> | 0.946 <sub>[0.90–0.98]</sub> | 92.0 <sub>[84–98]</sub> | 94.0 <sub>[86–100]</sub> | 0.932 <sub>[0.85–0.99]</sub> |
| tenders_v1 / all | bm25+thesaurus+rerank | 50 | 94.0 <sub>[88–100]</sub> | 98.0 <sub>[94–100]</sub> | 0.960 <sub>[0.91–1.00]</sub> | 0.943 <sub>[0.90–0.98]</sub> | 92.0 <sub>[84–98]</sub> | 94.0 <sub>[86–100]</sub> | 0.932 <sub>[0.85–0.99]</sub> |
| realworld_v2 / dev | bm25 | 35 | 91.4 <sub>[80–100]</sub> | 91.4 <sub>[80–100]</sub> | 0.933 <sub>[0.84–1.00]</sub> | 0.949 <sub>[0.88–1.00]</sub> | 82.9 <sub>[69–94]</sub> | 91.4 <sub>[80–100]</sub> | 0.883 <sub>[0.78–0.96]</sub> |
| realworld_v2 / dev | bm25+thesaurus | 35 | 77.1 <sub>[63–91]</sub> | 94.3 <sub>[86–100]</sub> | 0.862 <sub>[0.78–0.95]</sub> | 0.876 <sub>[0.79–0.95]</sub> | 71.4 <sub>[57–86]</sub> | 94.3 <sub>[86–100]</sub> | 0.817 <sub>[0.72–0.91]</sub> |
| realworld_v2 / dev | bm25+rerank | 35 | 94.3 <sub>[86–100]</sub> | 97.1 <sub>[91–100]</sub> | 0.956 <sub>[0.89–1.00]</sub> | 0.957 <sub>[0.89–1.00]</sub> | 94.3 <sub>[86–100]</sub> | 97.1 <sub>[91–100]</sub> | 0.956 <sub>[0.89–1.00]</sub> |
| realworld_v2 / dev | bm25+thesaurus+rerank | 35 | 82.9 <sub>[71–94]</sub> | 97.1 <sub>[91–100]</sub> | 0.898 <sub>[0.82–0.97]</sub> | 0.915 <sub>[0.84–0.98]</sub> | 82.9 <sub>[71–94]</sub> | 97.1 <sub>[91–100]</sub> | 0.898 <sub>[0.82–0.97]</sub> |
| realworld_v2 / test | bm25 | 35 | 88.6 <sub>[77–97]</sub> | 94.3 <sub>[86–100]</sub> | 0.917 <sub>[0.83–0.99]</sub> | 0.930 <sub>[0.85–0.99]</sub> | 82.9 <sub>[71–94]</sub> | 91.4 <sub>[80–100]</sub> | 0.880 <sub>[0.79–0.96]</sub> |
| realworld_v2 / test | bm25+thesaurus | 35 | 80.0 <sub>[66–91]</sub> | 94.3 <sub>[86–100]</sub> | 0.876 <sub>[0.78–0.96]</sub> | 0.890 <sub>[0.79–0.96]</sub> | 71.4 <sub>[57–86]</sub> | 91.4 <sub>[80–100]</sub> | 0.804 <sub>[0.69–0.91]</sub> |
| realworld_v2 / test | bm25+rerank | 35 | 94.3 <sub>[86–100]</sub> | 97.1 <sub>[91–100]</sub> | 0.963 <sub>[0.90–1.00]</sub> | 0.972 <sub>[0.93–1.00]</sub> | 94.3 <sub>[86–100]</sub> | 97.1 <sub>[91–100]</sub> | 0.963 <sub>[0.90–1.00]</sub> |
| realworld_v2 / test | bm25+thesaurus+rerank | 35 | 91.4 <sub>[83–100]</sub> | 97.1 <sub>[91–100]</sub> | 0.944 <sub>[0.88–1.00]</sub> | 0.958 <sub>[0.91–1.00]</sub> | 91.4 <sub>[83–100]</sub> | 97.1 <sub>[91–100]</sub> | 0.944 <sub>[0.88–1.00]</sub> |

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
  "name": "v3-dag",
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
  "lexicon_version": 2,
  "units_v2": true,
  "classifier": "lexicon",
  "rerank_version": 2,
  "product_terms_v2": true,
  "scope_guard": true,
  "dependency_mode": "dag",
  "detector_gate": true,
  "scoped_checklists": true,
  "vague_version": 2,
  "amendment_dedupe": true,
  "certification_scope": true,
  "relations_version": 2
}
```
