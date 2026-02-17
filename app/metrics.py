# app/metrics.py
from __future__ import annotations
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict

@dataclass
class Metrics:
    requests_total: int = 0
    errors_total: int = 0
    latency_ms_sum: float = 0.0
    latency_ms_count: int = 0
    method_usage: Dict[str, int] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def inc_request(self, method: str) -> None:
        with self._lock:
            self.requests_total += 1
            self.method_usage[method] = self.method_usage.get(method, 0) + 1

    def inc_error(self) -> None:
        with self._lock:
            self.errors_total += 1

    def observe_latency_ms(self, ms: float) -> None:
        with self._lock:
            self.latency_ms_sum += ms
            self.latency_ms_count += 1

    def avg_latency_ms(self) -> float:
        with self._lock:
            return (self.latency_ms_sum / self.latency_ms_count) if self.latency_ms_count else 0.0

metrics = Metrics()
