"""ApprovalStore protocol and InMemoryApprovalStore."""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from .request import ApprovalRequest, ApprovalResult


@runtime_checkable
class ApprovalStore(Protocol):
    """Persistence layer for approval requests and results."""

    def save(self, request: ApprovalRequest) -> None: ...
    def get(self, request_id: str) -> ApprovalRequest | None: ...
    def resolve(self, request_id: str, result: ApprovalResult) -> None: ...
    def get_result(self, request_id: str) -> ApprovalResult | None: ...
    def pending(self) -> list[ApprovalRequest]: ...
    def expire_old(self) -> int: ...


class InMemoryApprovalStore:
    """Thread-safe in-process approval store.

    Suitable for single-process applications and tests.
    """

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}
        self._results: dict[str, ApprovalResult] = {}
        self._lock = threading.Lock()

    def save(self, request: ApprovalRequest) -> None:
        with self._lock:
            self._requests[request.id] = request

    def get(self, request_id: str) -> ApprovalRequest | None:
        with self._lock:
            return self._requests.get(request_id)

    def resolve(self, request_id: str, result: ApprovalResult) -> None:
        with self._lock:
            self._results[request_id] = result

    def get_result(self, request_id: str) -> ApprovalResult | None:
        with self._lock:
            return self._results.get(request_id)

    def pending(self) -> list[ApprovalRequest]:
        """Return requests that have no result and are not expired."""
        now = datetime.now(timezone.utc)
        with self._lock:
            return [
                r for r in self._requests.values()
                if r.id not in self._results
                and (r.expires_at is None or r.expires_at > now)
            ]

    def expire_old(self) -> int:
        """Remove expired requests that have no result. Returns count removed."""
        now = datetime.now(timezone.utc)
        with self._lock:
            expired = [
                rid for rid, r in self._requests.items()
                if r.expires_at is not None
                and r.expires_at <= now
                and rid not in self._results
            ]
            for rid in expired:
                del self._requests[rid]
        return len(expired)
