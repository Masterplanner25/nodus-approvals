"""ApprovalRequest and ApprovalResult dataclasses."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ApprovalRequest:
    """A pending human-approval request for one agent action.

    Attributes
    ----------
    id:           Unique request identifier (UUID string).
    action:       Action being requested (e.g. ``"exec.bash"``, ``"send.dm"``).
    requester_id: Identity of the agent or user requesting approval.
    context:      Action-specific metadata (arguments, target, etc.).
    created_at:   UTC timestamp when the request was created.
    expires_at:   Optional expiry; None = never expires.
    metadata:     Additional free-form context.
    """

    id: str
    action: str
    requester_id: str
    context: dict[str, Any]
    created_at: datetime
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        action: str,
        requester_id: str,
        context: dict[str, Any] | None = None,
        *,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ApprovalRequest":
        return cls(
            id=str(uuid.uuid4()),
            action=action,
            requester_id=requester_id,
            context=dict(context or {}),
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            metadata=dict(metadata or {}),
        )

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class ApprovalResult:
    """The outcome of an approval request.

    Attributes
    ----------
    request_id:  ID of the ``ApprovalRequest`` this resolves.
    approved:    True if approved, False if denied.
    approver_id: Who approved/denied. None = policy auto-decision.
    timestamp:   UTC timestamp of the decision.
    reason:      Optional human-readable rationale.
    """

    request_id: str
    approved: bool
    approver_id: str | None = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    reason: str | None = None
