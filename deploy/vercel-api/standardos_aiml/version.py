"""Component versions recorded in every Provenance record.

Bump a component's version whenever its observable behaviour changes so stored
results can be traced back to the logic that produced them. The Python port
starts at 2.0.0: behaviour is identical to the TypeScript 1.0.0 engine (see
results/archive), but the implementation changed.
"""

COMPONENT_VERSIONS: dict[str, str] = {
    "ingest.parse": "2.0.0",
    "ingest.normalize": "3.0.0",
    "ingest.sections": "3.0.0",
    "nlp.requirements": "3.1.0",
    "nlp.classify": "3.0.0",
    "nlp.quantities": "3.1.0",
    "nlp.entities": "3.1.0",
    "standards.resolve": "2.0.0",
    "standards.retrieval": "3.0.0",
    "standards.rerank": "3.0.0",
    "standards.relations": "2.0.0",
    "standards.graph": "2.0.0",
    "reasoning.conflicts": "3.0.0",
    "reasoning.gaps": "3.0.0",
    "reasoning.dependencies": "3.1.0",
    "reasoning.versions": "3.0.0",
    "reasoning.certification": "3.1.0",
    "reasoning.verification": "2.0.0",
    "standards.dag": "3.0.0",
    "ml.classifier": "3.0.0",
    "repair.template": "2.0.0",
    "repair.llm": "2.0.0",
}

# 3.0.0: audit fixes behind PipelineConfig flags (preset "legacy-2.1" reproduces
# 2.1.0 exactly), dependency DAG, optional learned requirement classifiers.
# 3.1.0: generalisation fixes found on the open dev2 split (preset "v3.1", the default);
# preset "v3" still reproduces 3.0.0.
PIPELINE_VERSION = "standardos-pipeline/3.1.0-py"
