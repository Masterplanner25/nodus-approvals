from datetime import datetime, timezone, timedelta
from nodus_approvals import ApprovalRequest, ApprovalResult, InMemoryApprovalStore


def _req(action="exec.bash", expires_delta=None):
    expires_at = None
    if expires_delta is not None:
        expires_at = datetime.now(timezone.utc) + expires_delta
    return ApprovalRequest.create(action, "user-1", expires_at=expires_at)


def test_save_and_get():
    store = InMemoryApprovalStore()
    req = _req()
    store.save(req)
    assert store.get(req.id) is req


def test_get_unknown_returns_none():
    store = InMemoryApprovalStore()
    assert store.get("nonexistent") is None


def test_pending_includes_unresolved():
    store = InMemoryApprovalStore()
    req = _req()
    store.save(req)
    assert len(store.pending()) == 1


def test_pending_excludes_resolved():
    store = InMemoryApprovalStore()
    req = _req()
    store.save(req)
    store.resolve(req.id, ApprovalResult(req.id, approved=True))
    assert len(store.pending()) == 0


def test_pending_excludes_expired():
    store = InMemoryApprovalStore()
    req = _req(expires_delta=timedelta(seconds=-1))
    store.save(req)
    assert len(store.pending()) == 0


def test_expire_old_removes_expired():
    store = InMemoryApprovalStore()
    req = _req(expires_delta=timedelta(seconds=-1))
    store.save(req)
    count = store.expire_old()
    assert count == 1
    assert store.get(req.id) is None


def test_expire_old_leaves_valid():
    store = InMemoryApprovalStore()
    req = _req(expires_delta=timedelta(hours=1))
    store.save(req)
    count = store.expire_old()
    assert count == 0
    assert store.get(req.id) is not None
