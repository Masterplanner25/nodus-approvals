"""ApprovalPolicy — ordered rules mapping action patterns to approval modes."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field


class ApprovalMode:
    """Approval mode constants."""

    AUTO    = "auto"      # always approved immediately, no human needed
    DENY    = "deny"      # always denied immediately
    REQUIRE = "require"   # must be explicitly approved by a human
    PAIRING = "pairing"   # code-exchange approval (for new peer access)

    ALL = (AUTO, DENY, REQUIRE, PAIRING)


@dataclass
class ApprovalRule:
    """One rule in an ``ApprovalPolicy``.

    Attributes
    ----------
    action_pattern: fnmatch pattern matched against the action string.
                    Examples: ``"exec.*"``, ``"admin.*"``, ``"*"``.
    mode:           One of the ``ApprovalMode`` constants.
    approver_ids:   When mode is REQUIRE, these identities may approve.
                    Empty = any approver accepted.
    """

    action_pattern: str
    mode: str
    approver_ids: list[str] = field(default_factory=list)

    def matches(self, action: str) -> bool:
        return fnmatch.fnmatch(action, self.action_pattern)


class ApprovalPolicy:
    """Ordered list of ``ApprovalRule`` objects; first match wins.

    Usage::

        policy = ApprovalPolicy([
            ApprovalRule("exec.*", ApprovalMode.REQUIRE),
            ApprovalRule("admin.*", ApprovalMode.REQUIRE, approver_ids=["ops@"]),
            ApprovalRule("*", ApprovalMode.AUTO),
        ])
        rule = policy.resolve("exec.bash")
        # rule.mode == "require"
    """

    def __init__(self, rules: list[ApprovalRule]) -> None:
        self._rules = list(rules)

    def resolve(self, action: str) -> ApprovalRule:
        """Return the first rule that matches *action*.

        Falls back to ``ApprovalMode.REQUIRE`` if no rule matches.
        """
        for rule in self._rules:
            if rule.matches(action):
                return rule
        return ApprovalRule(action_pattern="*", mode=ApprovalMode.REQUIRE)

    def rules(self) -> list[ApprovalRule]:
        return list(self._rules)

    # ── Factory helpers ───────────────────────────────────────────────────────

    @classmethod
    def allow_all(cls) -> "ApprovalPolicy":
        """Approve every action automatically."""
        return cls([ApprovalRule("*", ApprovalMode.AUTO)])

    @classmethod
    def deny_all(cls) -> "ApprovalPolicy":
        """Deny every action immediately."""
        return cls([ApprovalRule("*", ApprovalMode.DENY)])

    @classmethod
    def require_for(cls, *patterns: str) -> "ApprovalPolicy":
        """Require approval for the given patterns; auto-approve everything else."""
        rules = [ApprovalRule(p, ApprovalMode.REQUIRE) for p in patterns]
        rules.append(ApprovalRule("*", ApprovalMode.AUTO))
        return cls(rules)
