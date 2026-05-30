import pytest
from nodus_approvals import (
    ApprovalGate,
    ApprovalMode,
    ApprovalPolicy,
    ApprovalRule,
    InMemoryApprovalStore,
)


def _gate(policy=None):
    return ApprovalGate(policy or ApprovalPolicy.allow_all(), InMemoryApprovalStore())


def test_auto_returns_approved_result():
    gate = _gate(ApprovalPolicy.allow_all())
    result = gate.check("exec.bash", "user-1")
    assert result is not None
    assert result.approved is True


def test_deny_returns_denied_result():
    gate = _gate(ApprovalPolicy.deny_all())
    result = gate.check("exec.bash", "user-1")
    assert result is not None
    assert result.approved is False


def test_require_returns_none_and_creates_request():
    store = InMemoryApprovalStore()
    gate = ApprovalGate(ApprovalPolicy.require_for("exec.*"), store)
    result = gate.check("exec.bash", "agent-1", context={"cmd": "ls"})
    assert result is None
    assert len(store.pending()) == 1
    req = store.pending()[0]
    assert req.action == "exec.bash"
    assert req.requester_id == "agent-1"


def test_approve_resolves_pending():
    store = InMemoryApprovalStore()
    gate = ApprovalGate(ApprovalPolicy.require_for("exec.*"), store)
    gate.check("exec.bash", "user-1")
    rid = gate.last_request_id
    result = gate.approve(rid, "ops-user")
    assert result.approved is True
    assert gate.poll(rid).approved is True


def test_deny_resolves_pending():
    store = InMemoryApprovalStore()
    gate = ApprovalGate(ApprovalPolicy.require_for("exec.*"), store)
    gate.check("exec.bash", "user-1")
    rid = gate.last_request_id
    gate.deny(rid, "ops-user", reason="too risky")
    result = gate.poll(rid)
    assert result.approved is False
    assert result.reason == "too risky"


def test_poll_returns_none_when_pending():
    store = InMemoryApprovalStore()
    gate = ApprovalGate(ApprovalPolicy.require_for("exec.*"), store)
    gate.check("exec.bash", "user-1")
    rid = gate.last_request_id
    assert gate.poll(rid) is None


def test_context_stored_in_request():
    store = InMemoryApprovalStore()
    gate = ApprovalGate(ApprovalPolicy.require_for("*"), store)
    gate.check("send.dm", "user-1", context={"peer": "alice"})
    req = store.pending()[0]
    assert req.context["peer"] == "alice"
