# Contamination log

Every inspection of a contaminated or blind split while making changes, and every blind scoring.

| When | Event | Items / splits | Reference |
| --- | --- | --- | --- |
| 2026-09-23 | v2.0 benchmark scored and inspected; ISI-mark fix made after scoring | tenders_v1/all | results/archive/tenders_v1-* |
| 2026-09-24 | Audit inspected heldout errors | component/heldout: t1, h15, y11 | docs/PIPELINE_AUDIT.md |
| 2026-09-24 | Audit inspected all dev/test errors | component/dev, component/test | docs/PIPELINE_AUDIT.md |
| 2026-09-24T03:32:21+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-033221_legacy-2.1` (legacy-2.1) |
| 2026-09-24 | realworld_v2 v2.1: dev gold-label fix (RCCB conformity wording); DOCX made deterministic; test content unchanged | realworld_v2/dev | datasets/manifest.json |
| 2026-09-24T03:45:52+00:00 | blind scoring (classifier comparison) | realworld_v2/test, component/heldout | results/classifiers/20260924-034602 |
| 2026-09-24T03:50:07+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035007_legacy-2.1` (legacy-2.1) |
| 2026-09-24T03:50:09+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035009_v3` (v3) |
| 2026-09-24T03:50:11+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035011_v3-dag` (v3-dag) |
| 2026-09-24T03:50:55+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035055_v3-hybrid` (v3-hybrid) |
| 2026-09-24T03:50:59+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035059_v3-gated` (v3-gated) |
| 2026-09-24T03:53:30+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035330_legacy-2.1` (legacy-2.1) |
| 2026-09-24T03:53:33+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035333_v3` (v3) |
| 2026-09-24T03:53:34+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035334_v3-dag` (v3-dag) |
| 2026-09-24T03:53:36+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035336_v3-dep-legacy` (v3-dep-legacy) |
| 2026-09-24T03:53:41+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035341_legacy+extraction` (legacy+extraction) |
| 2026-09-24T03:53:45+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035345_legacy+lexicon2` (legacy+lexicon2) |
| 2026-09-24T03:53:48+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035348_legacy+gating` (legacy+gating) |
| 2026-09-24T03:53:48+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035348_legacy+rerank2` (legacy+rerank2) |
| 2026-09-24T03:53:49+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035349_legacy+dep-citation` (legacy+dep-citation) |
| 2026-09-24T03:53:52+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035352_v3-tfidf` (v3-tfidf) |
| 2026-09-24T03:54:30+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035430_v3-hybrid` (v3-hybrid) |
| 2026-09-24T03:54:32+00:00 | blind scoring | component/heldout, realworld_v2/test | run `20260924-035432_v3-gated` (v3-gated) |
