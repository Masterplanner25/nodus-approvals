"""nodus-approvals — human-in-the-loop approval workflows.

A standard library for action approval: immediate policy decisions (auto/deny),
pending human approval (require), and code-exchange peer pairing.

Policy:
    ApprovalMode     — AUTO | DENY | REQUIRE | PAIRING constants
    ApprovalRule     — action_pattern + mode + optional approver_ids
    ApprovalPolicy   — ordered rules; first match wins
    declared_effects — the effect vocabulary a set of tool manifests uses
    tools_with_effects — tool names whose manifests declare a given effect

Requests:
    ApprovalRequest  — pending action approval (id, action, requester, context)
    ApprovalResult   — decision (approved/denied, approver, timestamp, reason)

Storage:
    ApprovalStore    — protocol for persistence backends
    InMemoryApprovalStore — thread-safe dict-backed store

Gate:
    ApprovalGate     — check / approve / deny / poll lifecycle

Pairing:
    generate_code    — cryptographically random N-digit code
    PairingEntry     — one pending/approved pairing
    PairingStore     — issue / validate / approve code lifecycle
"""
from .gate import ApprovalGate
from .pairing import PairingEntry, PairingStore, generate_code
from .policy import (
    ApprovalMode,
    ApprovalPolicy,
    ApprovalRule,
    declared_effects,
    tools_with_effects,
)
from .request import ApprovalRequest, ApprovalResult
from .store import ApprovalStore, InMemoryApprovalStore

__all__ = [
    # Policy
    "ApprovalMode",
    "ApprovalRule",
    "ApprovalPolicy",
    "declared_effects",
    "tools_with_effects",
    # Requests
    "ApprovalRequest",
    "ApprovalResult",
    # Storage
    "ApprovalStore",
    "InMemoryApprovalStore",
    # Gate
    "ApprovalGate",
    # Pairing
    "generate_code",
    "PairingEntry",
    "PairingStore",
]
