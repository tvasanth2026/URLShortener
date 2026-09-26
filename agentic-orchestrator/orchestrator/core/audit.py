"""Audit logging and reliability metrics.

Provides audit-grade observability: every state transition is appended to a
durable JSONL log with full decision lineage, and reliability metrics
(success rate, retry/rollback frequency, MTTR, end-to-end latency) are
derived from that log.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from typing import Dict, List

from .models import AuditEvent, utcnow


class AuditLog:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._events: List[AuditEvent] = []

    def log(self, event_type: str, task_id: str, detail: str) -> None:
        event = AuditEvent(event_type=event_type, task_id=task_id, detail=detail)
        self._events.append(event)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    def events(self) -> List[AuditEvent]:
        return list(self._events)


class MetricsRecorder:
    """Computes reliability metrics from an in-memory record of task timings/outcomes."""

    def __init__(self):
        self._task_start_times: Dict[str, float] = {}
        self._workflow_start: float = time.time()
        self.total_tasks = 0
        self.succeeded = 0
        self.failed = 0
        self.retries = 0
        self.rollbacks = 0
        self._recovery_start: Dict[str, float] = {}
        self._mttr_samples: List[float] = []

    def task_started(self, task_id: str) -> None:
        if task_id not in self._task_start_times:
            self.total_tasks += 1
        self._task_start_times[task_id] = time.time()

    def task_succeeded(self, task_id: str) -> None:
        self.succeeded += 1

    def task_failed(self, task_id: str) -> None:
        self.failed += 1
        self._recovery_start[task_id] = time.time()

    def task_retried(self, task_id: str) -> None:
        self.retries += 1

    def task_rolled_back(self, task_id: str) -> None:
        self.rollbacks += 1

    def task_recovered(self, task_id: str) -> None:
        start = self._recovery_start.pop(task_id, None)
        if start is not None:
            self._mttr_samples.append(time.time() - start)

    def snapshot(self) -> Dict[str, float]:
        attempted = self.succeeded + self.failed
        success_rate = (self.succeeded / attempted) if attempted else 1.0
        mttr_minutes = (sum(self._mttr_samples) / len(self._mttr_samples) / 60.0) if self._mttr_samples else 0.0
        e2e_latency_minutes = (time.time() - self._workflow_start) / 60.0
        return {
            "success_rate": round(success_rate, 4),
            "retry_count": self.retries,
            "rollback_count": self.rollbacks,
            "mttr_minutes": round(mttr_minutes, 2),
            "end_to_end_latency_minutes": round(e2e_latency_minutes, 2),
            "generated_at": utcnow(),
        }
