import time
from nodus_approvals import PairingStore, generate_code


def test_generate_code_length():
    code = generate_code(6)
    assert len(code) == 6
    assert code.isdigit()


def test_generate_code_different_each_time():
    codes = {generate_code() for _ in range(20)}
    assert len(codes) > 1   # at least some are different


def test_issue_returns_code():
    store = PairingStore()
    code = store.issue("peer-1")
    assert len(code) == 6
    assert code.isdigit()


def test_validate_returns_entry():
    store = PairingStore()
    code = store.issue("peer-1")
    entry = store.validate(code)
    assert entry is not None
    assert entry.peer_id == "peer-1"
    assert entry.approved is False


def test_validate_unknown_returns_none():
    store = PairingStore()
    assert store.validate("000000") is None


def test_approve_marks_approved():
    store = PairingStore()
    code = store.issue("peer-1")
    assert store.approve(code) is True
    entry = store.validate(code)
    assert entry.approved is True


def test_is_approved_true_after_approve():
    store = PairingStore()
    code = store.issue("peer-1")
    store.approve(code)
    assert store.is_approved("peer-1") is True


def test_is_approved_false_before_approve():
    store = PairingStore()
    store.issue("peer-1")
    assert store.is_approved("peer-1") is False


def test_issue_replaces_previous_code():
    store = PairingStore()
    code1 = store.issue("peer-1")
    code2 = store.issue("peer-1")
    assert store.validate(code1) is None   # old code gone
    assert store.validate(code2) is not None


def test_expire_old():
    store = PairingStore()
    store.issue("peer-1", ttl_seconds=0)
    time.sleep(0.01)
    count = store.expire_old()
    assert count == 1
