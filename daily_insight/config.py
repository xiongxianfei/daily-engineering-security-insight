from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from daily_insight.models import SourceConfig

_SOURCE_CONFIGS = TypeAdapter(list[SourceConfig])


def load_source_configs(path: Path) -> list[SourceConfig]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _SOURCE_CONFIGS.validate_python(payload)


def enabled_source_configs(sources: list[SourceConfig]) -> list[SourceConfig]:
    return [source for source in sources if source.enabled]


def required_source_configs(sources: list[SourceConfig]) -> list[SourceConfig]:
    return [source for source in enabled_source_configs(sources) if source.required_for_daily_run]
