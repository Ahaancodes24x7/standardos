"""Requirement classifiers compared against the lexicon.

* ``tfidf-lr``  — word (1–2) + character (3–5) TF-IDF, multinomial logistic regression
* ``embed-lr``  — frozen sentence embeddings (all-MiniLM-L6-v2), logistic regression
* ``hybrid-nn`` — PyTorch MLP over [sentence embedding ⊕ structured NLP features]
* ``gated``     — the lexicon when its margin-based confidence ≥ τ, otherwise hybrid-nn

Heavy dependencies (scikit-learn, torch, sentence-transformers) are optional:
they come with the ``ml`` extra and are imported lazily.
"""

from __future__ import annotations

import functools
from typing import Any, Sequence

import numpy as np

from .features import CATEGORIES, STRUCT_DIM

ENCODER = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384


@functools.lru_cache(maxsize=1)
def encoder() -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(ENCODER, device="cpu")


def embed(texts: Sequence[str]) -> np.ndarray:
    return np.asarray(encoder().encode(list(texts), batch_size=64, normalize_embeddings=True, show_progress_bar=False))


def build_hybrid(hidden: int = 256, dropout: float = 0.25) -> Any:
    import torch.nn as nn

    class HybridNet(nn.Module):
        """Two input towers (dense text embedding, sparse symbolic features) fused by an MLP."""

        def __init__(self) -> None:
            super().__init__()
            self.text = nn.Sequential(nn.Linear(EMBED_DIM, hidden), nn.GELU(), nn.Dropout(dropout))
            self.symbolic = nn.Sequential(nn.Linear(STRUCT_DIM, 64), nn.GELU(), nn.Dropout(dropout))
            self.head = nn.Sequential(
                nn.Linear(hidden + 64, 128), nn.GELU(), nn.Dropout(dropout), nn.Linear(128, len(CATEGORIES))
            )

        def forward(self, emb: Any, struct: Any) -> Any:
            import torch

            return self.head(torch.cat([self.text(emb), self.symbolic(struct)], dim=-1))

    return HybridNet()


def train_hybrid(
    emb: np.ndarray,
    struct: np.ndarray,
    y: np.ndarray,
    emb_val: np.ndarray,
    struct_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 300,
    seed: int = 7,
) -> tuple[Any, dict[str, Any]]:
    """Class-weighted cross-entropy, AdamW, early stopping on validation macro-F1."""
    import torch
    from sklearn.metrics import f1_score

    torch.manual_seed(seed)
    model = build_hybrid()
    counts = np.bincount(y, minlength=len(CATEGORIES)).astype(np.float32)
    weights = torch.tensor(np.where(counts > 0, counts.sum() / (len(CATEGORIES) * np.maximum(counts, 1)), 0.0), dtype=torch.float32)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-3)
    E, S, Y = (torch.tensor(emb, dtype=torch.float32), torch.tensor(struct, dtype=torch.float32), torch.tensor(y))
    Ev, Sv = torch.tensor(emb_val, dtype=torch.float32), torch.tensor(struct_val, dtype=torch.float32)
    best = (-1.0, 0, None)
    patience = 40
    for epoch in range(epochs):
        model.train()
        perm = torch.randperm(len(Y))
        for i in range(0, len(Y), 32):
            idx = perm[i : i + 32]
            opt.zero_grad()
            loss = loss_fn(model(E[idx], S[idx]), Y[idx])
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            pred = model(Ev, Sv).argmax(-1).numpy()
        f1 = f1_score(y_val, pred, average="macro", zero_division=0)
        if f1 > best[0]:
            best = (f1, epoch, {k: v.clone() for k, v in model.state_dict().items()})
        elif epoch - best[1] > patience:
            break
    model.load_state_dict(best[2])
    model.eval()
    return model, {"val_macro_f1": round(best[0], 4), "best_epoch": best[1]}


def predict_hybrid(model: Any, emb: np.ndarray, struct: np.ndarray) -> np.ndarray:
    import torch

    with torch.no_grad():
        logits = model(torch.tensor(emb, dtype=torch.float32), torch.tensor(struct, dtype=torch.float32))
        return torch.softmax(logits, -1).numpy()
