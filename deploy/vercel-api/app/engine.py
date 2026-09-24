"""Which pipeline configuration the API runs, and what the engine reports about itself."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from standardos_aiml.config import PRESETS, PipelineConfig, preset
from standardos_aiml.version import PIPELINE_VERSION

from .config import get_settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def pipeline_config() -> PipelineConfig:
    name = get_settings().standardos_pipeline_config
    if name not in PRESETS:
        log.warning("unknown STANDARDOS_PIPELINE_CONFIG %r; using v3.1", name)
        name = "v3.1"
    cfg = preset(name)
    if cfg.classifier != "lexicon":
        from standardos_aiml.ml.classifier import available

        if not available():
            log.warning("classifier %s unavailable (install the ml extra and train it); analyses keep lexicon categories", cfg.classifier)
    return cfg


def engine_info() -> dict[str, Any]:
    cfg = pipeline_config()
    info: dict[str, Any] = {
        "pipelineVersion": PIPELINE_VERSION,
        "config": cfg.name,
        "classifier": cfg.classifier,
        "dependencyMode": cfg.dependency_mode,
        "flags": {k: v for k, v in cfg.to_dict().items() if k not in ("name", "retrieval")},
        "presets": sorted(PRESETS),
    }
    if cfg.classifier != "lexicon":
        from standardos_aiml.ml.classifier import available

        info["classifierAvailable"] = available()
    return info
