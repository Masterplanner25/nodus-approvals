# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.2.0] — 2026-09-23

### Added

- **`ApprovalPolicy.require_for_effects(manifests, effects)`** — build a policy
  from what each tool *declares* rather than from a list of tool names. A tool
  whose manifest declares a gated effect requires approval because of what it
  declares, so there is no allowlist to keep in step; everything else is
  auto-approved. The effect vocabulary is the caller's — the coarse
  `nodus_lang_schema.VALID_EFFECTS` or a finer `fs.read` / `fs.write` split —
  and nothing is validated against a fixed set.

  The policy is a **snapshot** of the manifests at the call; rebuild it wherever
  the tool set changes.

  It **never returns a policy that gates nothing**. An effect that no manifest
  declares raises `ValueError`, because a typo (`"fs.wrte"`) is otherwise
  indistinguishable from "nothing needs approval" and the two have opposite
  consequences. Since every requested effect must be one some manifest declares,
  at least one tool always matches — the empty-policy case is unreachable by
  construction rather than guarded against. To pass a standard vocabulary to a
  registry that may not use all of it, intersect with `declared_effects()` first
  and call `allow_all()` when the result is empty.

- **`declared_effects(manifests)`** — the effect vocabulary a set of manifests
  uses. The escape hatch above, and a way to inspect what a registry declares.

- **`tools_with_effects(manifests, effects)`** — the matching tool names alone,
  in manifest order with repeats dropped, for logging what a gate will stop or
  asserting that a newly registered tool is covered.

- **15 tests** in `tests/test_policy_effects.py`. The six that constrain the
  refusal behaviour were falsified against the naive
  `require_for(*names) if names else allow_all()` implementation first, and are
  red against it.

### Fixed

- **Docs described an `ApprovalPolicy.evaluate()` that has never existed**, and
  gave its no-match fallback as `DENY`. The method is `resolve()` and the
  fallback is `REQUIRE` — an unrecognised action asks a human rather than being
  refused outright. Corrected in `README.md` and in the 0.1.0 entry below, which
  carried the same two errors.

---

## [0.1.0] — 2026-05-30

Initial release.

### Added

- **ApprovalMode** — `AUTO | DENY | REQUIRE | PAIRING` constants.

- **ApprovalRule** — `action_pattern` (fnmatch), `mode`, optional `approver_ids`.

- **ApprovalPolicy** — ordered rules; `resolve(action)` returns the first
  matching rule. Falls back to REQUIRE when no pattern matches.

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

[0.2.0]: https://github.com/Masterplanner25/nodus-approvals/releases/tag/v0.2.0
[0.1.0]: https://github.com/Masterplanner25/nodus-approvals/releases/tag/v0.1.0
