# Requirement classifier comparison `20260924-034602`

Trained on 136 unique requirement texts from open splits (realworld_v2/dev, component/dev); 34 held out for early stopping and the gate threshold (τ = 0.675). Encoder `sentence-transformers/all-MiniLM-L6-v2` (frozen). Hybrid network: {'val_macro_f1': 0.9282, 'best_epoch': 25, 'train_seconds': 1.0}.

Accuracy / macro-F1 in %, 95% bootstrap CI of macro-F1 in brackets.

| Test set | n | lexicon-v2 | tfidf-lr | embed-lr | hybrid-nn | gated |
| --- | --- | --- | --- | --- | --- | --- |
| realworld_v2/test | 526 | 80.8 / **83.1** <sub>[80–86]</sub> | 81.9 / **86.2** <sub>[84–89]</sub> | 86.1 / **89.2** <sub>[87–91]</sub> | 89.0 / **90.9** <sub>[88–93]</sub> | 84.2 / **86.6** <sub>[84–89]</sub> |
| tenders_v1/all | 176 | 75.6 / **76.5** <sub>[69–82]</sub> | 81.2 / **80.3** <sub>[72–86]</sub> | 79.0 / **78.7** <sub>[70–84]</sub> | 84.1 / **83.7** <sub>[76–89]</sub> | 80.1 / **79.5** <sub>[73–85]</sub> |
| component/test | 22 | 81.8 / **76.0** <sub>[56–96]</sub> | 68.2 / **43.9** <sub>[28–76]</sub> | 59.1 / **41.8** <sub>[26–59]</sub> | 72.7 / **51.3** <sub>[40–75]</sub> | 86.4 / **70.6** <sub>[54–100]</sub> |
| component/heldout | 12 | 100.0 / **100.0** <sub>[100–100]</sub> | 66.7 / **56.5** <sub>[29–84]</sub> | 66.7 / **63.8** <sub>[34–92]</sub> | 75.0 / **82.1** <sub>[49–100]</sub> | 91.7 / **94.0** <sub>[75–100]</sub> |

## Per-class F1

### realworld_v2/test

| Class | lexicon-v2 | tfidf-lr | embed-lr | hybrid-nn | gated |
| --- | --- | --- | --- | --- | --- |
| certification | 100 | 100 | 100 | 100 | 100 |
| dimensional | 68 | 100 | 91 | 86 | 88 |
| documentation | 87 | 87 | 65 | 76 | 87 |
| electrical | 71 | 82 | 88 | 90 | 78 |
| environmental | 99 | 94 | 100 | 100 | 99 |
| general | 54 | 55 | 76 | 73 | 66 |
| installation | 79 | 88 | 95 | 87 | 72 |
| material | 77 | 88 | 82 | 82 | 77 |
| performance | 89 | 83 | 97 | 100 | 92 |
| quality | 89 | 91 | 94 | 99 | 95 |
| safety | 89 | 100 | 100 | 100 | 89 |
| testing | 97 | 67 | 81 | 97 | 97 |

### tenders_v1/all

| Class | lexicon-v2 | tfidf-lr | embed-lr | hybrid-nn | gated |
| --- | --- | --- | --- | --- | --- |
| certification | 77 | 80 | 80 | 100 | 83 |
| dimensional | 80 | 67 | 80 | 67 | 80 |
| documentation | 78 | 78 | 64 | 76 | 67 |
| electrical | 77 | 83 | 86 | 91 | 86 |
| environmental | 88 | 86 | 85 | 92 | 92 |
| general | 51 | 64 | 58 | 65 | 44 |
| installation | 57 | 62 | 67 | 62 | 60 |
| material | 76 | 90 | 74 | 76 | 84 |
| performance | 98 | 90 | 89 | 94 | 100 |
| quality | 91 | 100 | 86 | 100 | 100 |
| safety | 75 | 83 | 93 | 93 | 77 |
| testing | 71 | 83 | 84 | 88 | 81 |

### component/test

| Class | lexicon-v2 | tfidf-lr | embed-lr | hybrid-nn | gated |
| --- | --- | --- | --- | --- | --- |
| certification | 100 | 67 | 100 | 100 | 100 |
| documentation | 100 | 0 | 0 | 0 | 0 |
| electrical | 80 | 75 | 80 | 100 | 100 |
| environmental | 100 | 100 | 80 | 100 | 100 |
| general | 50 | 0 | 0 | 33 | 50 |
| material | 50 | 40 | 0 | 0 | 67 |
| performance | 89 | 67 | 67 | 89 | 89 |
| quality | 91 | 91 | 91 | 91 | 100 |
| testing | 100 | 0 | 0 | 0 | 100 |

### component/heldout

| Class | lexicon-v2 | tfidf-lr | embed-lr | hybrid-nn | gated |
| --- | --- | --- | --- | --- | --- |
| dimensional | 100 | 67 | 67 | 67 | 100 |
| documentation | 100 | 100 | 100 | 100 | 100 |
| electrical | 100 | 67 | 100 | 67 | 100 |
| environmental | 100 | 100 | 100 | 100 | 100 |
| general | 100 | 0 | 50 | 67 | 67 |
| material | 100 | 75 | 57 | 57 | 86 |
| performance | 100 | 0 | 0 | 100 | 100 |
| testing | 100 | 100 | 100 | 100 | 100 |

