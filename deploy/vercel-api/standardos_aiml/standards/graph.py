"""The standards knowledge graph and the per-analysis evidence graph.

The graph is small (tens to low thousands of nodes) and typed, and every query
needed is a bounded traversal (depth ≤ 3) from a handful of seeds. It is held
as adjacency lists over the relational tables rather than in a separate graph
database; see docs/INTELLIGENCE.md for the trade-off.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Optional

from ..types import (
    AnalysisGraph,
    Corpus,
    CorpusRelationship,
    GraphEdge,
    GraphNode,
    RequirementMapping,
    StructuredRequirement,
)


@dataclass
class Replacement:
    id: str
    path: list[CorpusRelationship]


@dataclass
class Dependency:
    id: str
    type: str
    path: list[CorpusRelationship]


class StandardsGraph:
    def __init__(self, corpus: Corpus) -> None:
        self.corpus = corpus
        self._out: dict[str, list[CorpusRelationship]] = {}
        self._in: dict[str, list[CorpusRelationship]] = {}
        for rel in corpus.relationships:
            self._out.setdefault(rel.from_id, []).append(rel)
            self._in.setdefault(rel.to_id, []).append(rel)

    def outgoing(self, standard_id: str, types: Optional[Iterable[str]] = None) -> list[CorpusRelationship]:
        allowed = set(types) if types is not None else None
        return [r for r in self._out.get(standard_id, []) if allowed is None or r.type in allowed]

    def incoming(self, standard_id: str, types: Optional[Iterable[str]] = None) -> list[CorpusRelationship]:
        allowed = set(types) if types is not None else None
        return [r for r in self._in.get(standard_id, []) if allowed is None or r.type in allowed]

    def latest_replacement(self, standard_id: str) -> Optional[Replacement]:
        """The record that supersedes ``standard_id``, following chains (A → B → C) to the latest."""
        path: list[CorpusRelationship] = []
        current = standard_id
        visited = {standard_id}
        while True:
            incoming = self.incoming(current, ["SUPERSEDES"])
            nxt = incoming[0] if incoming else None
            if not nxt or nxt.from_id in visited:
                break
            path.append(nxt)
            visited.add(nxt.from_id)
            current = nxt.from_id
        return Replacement(current, path) if path else None

    def dependencies(self, standard_id: str, depth: int = 2) -> list[Dependency]:
        """Standards reachable through REQUIRES / TESTED_BY edges, breadth-first up to ``depth``."""
        result: list[Dependency] = []
        queue: deque[tuple[str, list[CorpusRelationship]]] = deque([(standard_id, [])])
        seen = {standard_id}
        while queue:
            node, path = queue.popleft()
            if len(path) >= depth:
                continue
            for rel in self.outgoing(node, ["REQUIRES", "TESTED_BY"]):
                if rel.to_id in seen:
                    continue
                seen.add(rel.to_id)
                next_path = [*path, rel]
                result.append(Dependency(rel.to_id, rel.type, next_path))
                queue.append((rel.to_id, next_path))
        return result


def build_analysis_graph(
    corpus: Corpus,
    graph: StandardsGraph,
    requirements: list[StructuredRequirement],
    mappings: list[RequirementMapping],
    applicable: list[str],
) -> AnalysisGraph:
    """Per-analysis evidence graph.

    Requirements → mapped clauses → standards → their dependencies and
    certification schemes. Persisted with the run so the UI can render the
    path behind each finding.
    """
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    edge_ids: set[str] = set()
    by_req = {r.id: r for r in requirements}

    def add_standard(standard_id: str):
        s = corpus.standard(standard_id)
        if s and standard_id not in nodes:
            nodes[standard_id] = GraphNode(standard_id, "standard", s.number, s.title)
        return s

    def push(edge: GraphEdge) -> None:
        edges.append(edge)
        edge_ids.add(edge.id)

    for mapping in mappings:
        req = by_req.get(mapping.requirement_id)
        top = mapping.hits[0] if mapping.hits else None
        if not req or not top:
            continue
        nodes[req.id] = GraphNode(req.id, "requirement", req.id.upper(), req.text)
        s = add_standard(top.standard_id)
        clause = next((c for c in s.clauses if c.id == top.clause_id), None) if s else None
        if s and clause:
            nodes[clause.id] = GraphNode(
                clause.id, "clause", f"Cl. {clause.ref}" if clause.ref else clause.heading, clause.text
            )
            push(GraphEdge(f"map-{req.id}", "MAPS_TO", req.id, clause.id, top.confidence, mapping.basis))
            push(GraphEdge(f"has-{clause.id}", "HAS_CLAUSE", s.id, clause.id, 1, "corpus"))

    for standard_id in applicable:
        s = add_standard(standard_id)
        if not s:
            continue
        for dep in graph.dependencies(standard_id, 2):
            add_standard(dep.id)
            for rel in dep.path:
                add_standard(rel.from_id)
                if rel.id not in edge_ids:
                    push(GraphEdge(rel.id, rel.type, rel.from_id, rel.to_id, rel.confidence, rel.method))
        for rel in [
            *graph.outgoing(standard_id, ["REFERENCES", "SUPERSEDES", "RELATED_TO"]),
            *graph.incoming(standard_id, ["SUPERSEDES"]),
        ]:
            add_standard(rel.from_id)
            add_standard(rel.to_id)
            if rel.id not in edge_ids:
                push(GraphEdge(rel.id, rel.type, rel.from_id, rel.to_id, rel.confidence, rel.method))
        if s.certification.scheme:
            cert_id = f"cert:{s.id}"
            nodes[cert_id] = GraphNode(cert_id, "certification", "BIS certification", s.certification.scheme)
            push(GraphEdge(f"cert-{s.id}", "CERTIFIED_BY", s.id, cert_id, 0.8, "corpus"))
    return AnalysisGraph(list(nodes.values()), edges)
