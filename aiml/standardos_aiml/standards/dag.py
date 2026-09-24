"""Normative dependency DAG, built alongside the typed standards graph.

The typed graph (``graph.py``) stores every curated edge, including supersession
and informative references. For obligation reasoning only two edge types matter:
REQUIRES and TESTED_BY. This module builds a directed acyclic view of them:

1. **Supersession contraction** — each standard is replaced by the latest
   standard that supersedes it, so "IS 516:1959" and "IS 516 (Part 1/Sec 1):2021"
   are one node and edges into withdrawn standards point at their replacements.
2. **Cycle detection** — strongly connected components (Tarjan); any cycle is
   reported as a corpus-curation problem and collapsed into one node.
3. **Order and closure** — topological layers, transitive closure (with the
   shortest path to each dependency) and transitive reduction.
4. **Ancestors** — every standard whose obligations transitively include a given
   standard, used for change impact ("which documents are affected when X is
   revised").
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable, Optional

from ..types import Corpus, CorpusRelationship
from .graph import StandardsGraph

NORMATIVE = ("REQUIRES", "TESTED_BY")


@dataclass
class DagEdge:
    source: str
    target: str
    type: str
    relationship: CorpusRelationship


@dataclass
class Reach:
    target: str
    path: list[DagEdge]  # shortest path from the source

    @property
    def depth(self) -> int:
        return len(self.path)

    @property
    def first_type(self) -> str:
        return self.path[0].type


@dataclass
class DependencyDAG:
    corpus: Corpus
    graph: StandardsGraph
    min_confidence: float = 0.7
    canonical: dict[str, str] = field(default_factory=dict)
    edges: dict[str, list[DagEdge]] = field(default_factory=dict)
    reverse: dict[str, list[DagEdge]] = field(default_factory=dict)
    cycles: list[list[str]] = field(default_factory=list)
    layer: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for std in self.corpus.standards:
            latest = self.graph.latest_replacement(std.id)
            self.canonical[std.id] = latest.id if latest else std.id
        for rel in self.corpus.relationships:
            if rel.type not in NORMATIVE or rel.confidence < self.min_confidence:
                continue
            src, dst = self.canon(rel.from_id), self.canon(rel.to_id)
            if src == dst:
                continue
            edge = DagEdge(src, dst, rel.type, rel)
            self.edges.setdefault(src, []).append(edge)
            self.reverse.setdefault(dst, []).append(edge)
        self.cycles = [c for c in self._scc() if len(c) > 1]
        self._layers()

    # -- structure -----------------------------------------------------------

    def canon(self, standard_id: str) -> str:
        return self.canonical.get(standard_id, standard_id)

    @property
    def nodes(self) -> list[str]:
        return sorted({self.canon(s.id) for s in self.corpus.standards})

    def _scc(self) -> list[list[str]]:
        index: dict[str, int] = {}
        low: dict[str, int] = {}
        stack: list[str] = []
        on_stack: set[str] = set()
        out: list[list[str]] = []
        counter = [0]

        def strong(v: str) -> None:
            index[v] = low[v] = counter[0]
            counter[0] += 1
            stack.append(v)
            on_stack.add(v)
            for e in self.edges.get(v, []):
                if e.target not in index:
                    strong(e.target)
                    low[v] = min(low[v], low[e.target])
                elif e.target in on_stack:
                    low[v] = min(low[v], index[e.target])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                out.append(comp)

        for node in self.nodes:
            if node not in index:
                strong(node)
        return out

    def _layers(self) -> None:
        """Layer 0 = standards with no normative dependencies; layer n depends on layer < n."""
        in_cycle = {n for c in self.cycles for n in c}
        memo: dict[str, int] = {}

        def depth(n: str, seen: frozenset[str]) -> int:
            if n in memo:
                return memo[n]
            succ = [e.target for e in self.edges.get(n, []) if e.target not in seen and e.target not in in_cycle]
            memo[n] = 0 if not succ else 1 + max(depth(t, seen | {n}) for t in succ)
            return memo[n]

        for node in self.nodes:
            self.layer[node] = depth(node, frozenset())

    # -- queries -------------------------------------------------------------

    def closure(self, standard_id: str, first_hop: Optional[Iterable[str]] = None) -> dict[str, Reach]:
        """Every normative dependency reachable from ``standard_id`` (shortest path first).

        ``first_hop`` restricts the edge types allowed on the first hop (product
        standards bind the purchaser only through TESTED_BY); later hops follow the
        dependency's own normative edges.
        """
        start = self.canon(standard_id)
        allowed_first = set(first_hop) if first_hop is not None else set(NORMATIVE)
        out: dict[str, Reach] = {}
        queue: deque[tuple[str, list[DagEdge]]] = deque([(start, [])])
        seen = {start}
        while queue:
            node, path = queue.popleft()
            for e in self.edges.get(node, []):
                if not path and e.type not in allowed_first:
                    continue
                if e.target in seen:
                    continue
                seen.add(e.target)
                reach = Reach(e.target, [*path, e])
                out[e.target] = reach
                queue.append((e.target, reach.path))
        return out

    def ancestors(self, standard_id: str) -> set[str]:
        """Standards whose normative closure contains ``standard_id``."""
        target = self.canon(standard_id)
        out: set[str] = set()
        queue = deque([target])
        while queue:
            node = queue.popleft()
            for e in self.reverse.get(node, []):
                if e.source not in out:
                    out.add(e.source)
                    queue.append(e.source)
        return out

    def transitive_reduction(self) -> list[DagEdge]:
        """Edges not implied by a longer path (the minimal DAG with the same reachability)."""
        kept = []
        for src, edges in self.edges.items():
            for e in edges:
                others = [x for x in edges if x is not e and x.target != e.target]
                implied = any(e.target in self.closure(x.target) for x in others)
                if not implied:
                    kept.append(e)
        return kept

    def stats(self) -> dict[str, object]:
        closure_edges = sum(len(self.closure(n)) for n in self.nodes)
        direct_edges = sum(len(v) for v in self.edges.values())
        return {
            "nodes": len(self.nodes),
            "normative_edges": direct_edges,
            "closure_pairs": closure_edges,
            "transitive_only_pairs": closure_edges - len({(e.source, e.target) for v in self.edges.values() for e in v}),
            "max_layer": max(self.layer.values()) if self.layer else 0,
            "cycles": self.cycles,
            "reduction_edges": len(self.transitive_reduction()),
            "contracted": {k: v for k, v in self.canonical.items() if k != v},
        }

    def to_dict(self) -> dict[str, object]:
        """JSON view for the API: nodes with layers, reduced edges, cycles."""
        return {
            "nodes": [
                {"id": n, "number": (s.number if (s := self.corpus.standard(n)) else n), "layer": self.layer.get(n, 0)}
                for n in self.nodes
                if n in self.edges or n in self.reverse
            ],
            "edges": [
                {"from": e.source, "to": e.target, "type": e.type, "relationship": e.relationship.id}
                for e in self.transitive_reduction()
            ],
            "cycles": self.cycles,
            "contracted": {k: v for k, v in self.canonical.items() if k != v},
        }
