from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Dict


@dataclass
class MetricsBucket:
    requests_total: int = 0
    errors_total: int = 0
    total_tokens: int = 0
    latency_ms_sum: float = 0.0
    latency_ms_count: int = 0
    method_usage: Dict[str, int] = field(default_factory=dict)

    def avg_latency_ms(self) -> float:
        return (self.latency_ms_sum / self.latency_ms_count) if self.latency_ms_count else 0.0

    def snapshot(self) -> dict:
        return {
            "requests_total": self.requests_total,
            "errors_total": self.errors_total,
            "total_tokens": self.total_tokens,
            "avg_latency_ms": round(self.avg_latency_ms(), 3),
            "method_usage": dict(self.method_usage),
        }


@dataclass
class Metrics(MetricsBucket):
    skill_selection: MetricsBucket = field(default_factory=MetricsBucket)
    project_selection: MetricsBucket = field(default_factory=MetricsBucket)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def _subsystem_bucket(self, subsystem: str) -> MetricsBucket:
        if subsystem == "skill_selection":
            return self.skill_selection
        if subsystem == "project_selection":
            return self.project_selection
        raise ValueError(f"Unsupported metrics subsystem: {subsystem}")

    def inc_request(self, method: str, subsystem: str = "skill_selection") -> None:
        with self._lock:
            self.requests_total += 1
            self.method_usage[method] = self.method_usage.get(method, 0) + 1

            bucket = self._subsystem_bucket(subsystem)
            bucket.requests_total += 1
            bucket.method_usage[method] = bucket.method_usage.get(method, 0) + 1

    def inc_error(self, subsystem: str = "skill_selection") -> None:
        with self._lock:
            self.errors_total += 1
            self._subsystem_bucket(subsystem).errors_total += 1

    def observe_tokens(self, tokens: int, subsystem: str = "skill_selection") -> None:
        if tokens <= 0:
            return
        with self._lock:
            self.total_tokens += tokens
            self._subsystem_bucket(subsystem).total_tokens += tokens

    def observe_latency_ms(self, ms: float, subsystem: str = "skill_selection") -> None:
        with self._lock:
            self.latency_ms_sum += ms
            self.latency_ms_count += 1
            bucket = self._subsystem_bucket(subsystem)
            bucket.latency_ms_sum += ms
            bucket.latency_ms_count += 1

    def avg_latency_ms(self) -> float:
        with self._lock:
            return (self.latency_ms_sum / self.latency_ms_count) if self.latency_ms_count else 0.0

    def subsystem_snapshots(self) -> dict[str, dict]:
        with self._lock:
            return {
                "skill_selection": self.skill_selection.snapshot(),
                "project_selection": self.project_selection.snapshot(),
            }


metrics = Metrics()
