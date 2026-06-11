# nodus-approvals

**Human-in-the-loop approval workflows for Nodus AI systems.**

Policy-driven action gating with auto/deny/require/pairing modes, a full
request lifecycle, and cryptographic peer-pairing codes. No required
external dependencies — pure stdlib.

> **Status:** v0.1.0 — published on [PyPI](https://pypi.org/project/nodus-approvals/).

---

## Install

```bash
pip install nodus-approvals
```

---

## What it provides

| Component | Purpose |
|---|---|
| `ApprovalPolicy` / `ApprovalRule` | fnmatch-pattern rules; first match wins |
| `ApprovalRequest` / `ApprovalResult` | Pending action + decision record |
| `InMemoryApprovalStore` | Thread-safe request storage |
| `ApprovalGate` | check / approve / deny / poll lifecycle |
| `PairingStore` / `generate_code` | 6-digit code exchange for peer pairing |

---

## Quick start

```python
from nodus_approvals import ApprovalGate, ApprovalPolicy, ApprovalRule, ApprovalMode

policy = ApprovalPolicy(rules=[
    ApprovalRule(action_pattern="admin.*", mode=ApprovalMode.REQUIRE),
    ApprovalRule(action_pattern="read.*",  mode=ApprovalMode.AUTO),
    ApprovalRule(action_pattern="*",       mode=ApprovalMode.DENY),
])

gate = ApprovalGate(policy=policy)

result = gate.check("read.memory", requester_id="u1")
# result.approved == True  (matched AUTO rule)

result = gate.check("admin.delete", requester_id="u1")
# result.approved == False, result.pending == True  (REQUIRE — needs human)

gate.approve(result.request_id, approver_id="admin-1")
```

---

## Approval modes

| Mode | Behaviour |
|---|---|
| `AUTO` | Immediately approved; no human required |
| `DENY` | Immediately denied |
| `REQUIRE` | Creates a pending `ApprovalRequest`; blocks until approved or denied |
| `PAIRING` | Requires a valid pairing code exchange before approval |

---

## ApprovalPolicy

Rules are evaluated in order; the first matching rule wins. Patterns use
`fnmatch` — `*` matches any sequence, `?` matches one character.

```python
policy = ApprovalPolicy(rules=[
    ApprovalRule("payments.*",  ApprovalMode.REQUIRE, approver_ids=["finance"]),
    ApprovalRule("reports.*",   ApprovalMode.AUTO),
    ApprovalRule("*",           ApprovalMode.DENY),
])
```

`policy.evaluate(action)` returns the matching `ApprovalRule` (or the default
DENY rule if no pattern matches).

---

## ApprovalGate

```python
gate = ApprovalGate(policy=policy, store=my_store)  # store defaults to InMemory

result = gate.check("some.action", requester_id="u1", context={"key": "val"})
# result.approved  — True/False
# result.pending   — True if REQUIRE mode and awaiting human decision
# result.request_id — present when pending

gate.approve(request_id, approver_id="approver-1", reason="looks good")
gate.deny(request_id,    approver_id="approver-1", reason="not authorised")
gate.poll(request_id)    # ApprovalResult | None — check current decision
```

---

## Pairing codes

```python
from nodus_approvals import PairingStore, generate_code

store = PairingStore(code_length=6, ttl_seconds=300)
code = store.issue(peer_id="peer-abc")        # e.g. "847291"
entry = store.validate(code)                   # PairingEntry | None
store.approve(code, approver_id="admin-1")    # mark as approved
```

`generate_code(length=6)` produces a cryptographically random numeric code.
Expired entries are automatically excluded from `validate`.

---

## InMemoryApprovalStore

```python
from nodus_approvals import InMemoryApprovalStore, ApprovalRequest

store = InMemoryApprovalStore()
req = ApprovalRequest(action="admin.delete", requester_id="u1")
store.save(req)
store.get(req.id)
store.list_pending()
store.list_by_requester("u1")
```

---

## Design

- **No required dependencies.** Pure stdlib (`fnmatch`, `secrets`, `threading`,
  `dataclasses`, `datetime`, `uuid`).
- **Thread-safe.** `InMemoryApprovalStore` and `PairingStore` use `threading.Lock`.
- **Pluggable storage.** Any class satisfying the `ApprovalStore` protocol works.

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -q
```

---

## License

MIT — see [LICENSE](LICENSE).
