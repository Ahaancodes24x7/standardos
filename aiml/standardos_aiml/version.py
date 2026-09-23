"""Component versions recorded in every Provenance record.

Bump a component's version whenever its observable behaviour changes so stored
results can be traced back to the logic that produced them. The Python port
starts at 2.0.0: behaviour is identical to the TypeScript 1.0.0 engine (see
aiml/eval/results/parity.md), but the implementation changed.
"""

COMPONENT_VERSIONS: dict[str, str] = {
    "ingest.parse": "2.0.0",
    "ingest.normalize": "2.0.0",
    "ingest.sections": "2.0.0",
    "nlp.requirements": "2.0.0",
    "nlp.classify": "2.0.0",
    "nlp.quantities": "2.0.0",
    "nlp.entities": "2.1.0",
    "standards.resolve": "2.0.0",
    "standards.retrieval": "2.0.0",
    "standards.rerank": "2.0.0",
    "standards.relations": "2.0.0",
    "standards.graph": "2.0.0",
    "reasoning.conflicts": "2.0.0",
    "reasoning.gaps": "2.0.0",
    "reasoning.dependencies": "2.0.0",
    "reasoning.versions": "2.0.0",
    "reasoning.certification": "2.0.0",
    "reasoning.verification": "2.0.0",
    "repair.template": "2.0.0",
    "repair.llm": "2.0.0",
}

PIPELINE_VERSION = "standardos-pipeline/2.1.0-py"
