"""Simple retrieval metrics helper used by memory adapters and backfill scripts.
Writes metrics to stdout and optionally to a JSON file.
"""
from __future__ import annotations
import time
import json
from typing import Dict, Any, Optional


class Metrics:
    def __init__(self):
        self._metrics: Dict[str, Any] = {}

    def inc(self, key: str, amount: int = 1):
        self._metrics[key] = self._metrics.get(key, 0) + amount

    def set(self, key: str, value: Any):
        self._metrics[key] = value

    def observe_timing(self, key: str, start_ts: float):
        self._metrics[key] = (time.time() - start_ts)

    def snapshot(self) -> Dict[str, Any]:
        return dict(self._metrics)

    def write_json(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.snapshot(), f, indent=2)


# convenience module-level instance
metrics = Metrics()
