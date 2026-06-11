# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] — 2026-05-30

Initial release.

### Added

- **ApprovalMode** — `AUTO | DENY | REQUIRE | PAIRING` constants.

- **ApprovalRule** — `action_pattern` (fnmatch), `mode`, optional `approver_ids`.

- **ApprovalPolicy** — ordered rules; `evaluate(action)` returns the first
  matching rule. Default rule is DENY when no pattern matches.

- **ApprovalRequest** — pending action approval record. Fields: `id`, `action`,
  `requester_id`, `context`, `created_at`, `status`.

- **ApprovalResult** — decision record. Fields: `request_id`, `approved`,
  `pending`, `approver_id`, `timestamp`, `reason`.

- **ApprovalStore** (protocol) + **InMemoryApprovalStore** — thread-safe
  dict-backed store. `save`, `get`, `list_pending`, `list_by_requester`.

- **ApprovalGate** — full request lifecycle.
  `check(action, requester_id, context?)` — evaluates policy and returns an
  `ApprovalResult` (immediately for AUTO/DENY; pending for REQUIRE).
  `approve(request_id, approver_id, reason?)` — records approval.
  `deny(request_id, approver_id, reason?)` — records denial.
  `poll(request_id)` — returns current `ApprovalResult | None`.

- **`generate_code(length)`** — cryptographically random numeric code via
  `secrets`.

- **PairingEntry** — one pending/approved pairing. Fields: `peer_id`, `code`,
  `issued_at`, `expires_at`, `approved`, `approver_id`.

- **PairingStore** — code exchange lifecycle. `issue(peer_id)` → code string.
  `validate(code)` → `PairingEntry | None` (None if expired or not found).
  `approve(code, approver_id)` → marks pairing as approved.

- **32 tests** across four test files (gate, pairing, policy, store).

- **No required dependencies** — pure stdlib.

[0.1.0]: https://github.com/Masterplanner25/nodus-approvals/releases/tag/v0.1.0
