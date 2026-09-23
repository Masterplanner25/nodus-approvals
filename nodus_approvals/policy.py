"""ApprovalPolicy — ordered rules mapping action patterns to approval modes."""
from __future__ import annotations

import fnmatch
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any


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


def _effect_set(value: Any, where: str) -> frozenset[str]:
    """Coerce a manifest's ``effects`` (or a caller's) to a set of effect names.

    A bare ``str`` is refused rather than iterated. ``frozenset("fs.write")`` is a
    set of eleven *characters* that matches nothing, so iterating one would turn a
    plausible typo into a policy that gates nothing — the exact silent failure
    ``require_for_effects`` exists to make impossible.
    """
    if isinstance(value, str):
        raise ValueError(
            f"{where} must be a collection of effect names, not a single string; "
            f"pass [{value!r}] rather than {value!r}"
        )
    try:
        return frozenset(value)
    except TypeError as exc:
        raise ValueError(f"{where} must be iterable, got {type(value).__name__}") from exc


def declared_effects(manifests: Iterable[Mapping[str, Any]]) -> frozenset[str]:
    """Every effect name any of *manifests* declares — the vocabulary in play.

    The effect vocabulary is the caller's: this library never validates against a
    fixed set, so a host may use ``nodus_lang_schema.VALID_EFFECTS``
    (``pure``/``reads_state``/``writes_state``/``network``/``filesystem``/
    ``spawns_task``) or a finer one such as ``fs.read`` / ``fs.write``. This is
    what makes such a vocabulary inspectable — and it is the escape hatch when
    ``require_for_effects`` refuses an effect no tool declares::

        gated = set(MY_VOCABULARY) & declared_effects(manifests)
    """
    observed: set[str] = set()
    for index, manifest in enumerate(manifests):
        observed |= _effect_set(manifest.get("effects", ()), f"manifests[{index}]['effects']")
    return frozenset(observed)


def tools_with_effects(
    manifests: Iterable[Mapping[str, Any]],
    effects: Iterable[str],
) -> list[str]:
    """Names of the tools whose declared effects intersect *effects*.

    Manifest order is preserved and repeats are dropped, so the result can be
    handed straight to :meth:`ApprovalPolicy.require_for` without producing
    duplicate rules.

    Exported because a host may want the names for something other than a policy
    — logging what a gate will stop, or asserting in a test that a tool it just
    registered is covered.
    """
    gated = _effect_set(effects, "effects")
    names: list[str] = []
    seen: set[str] = set()
    for index, manifest in enumerate(manifests):
        if not _effect_set(manifest.get("effects", ()), f"manifests[{index}]['effects']") & gated:
            continue
        name = manifest.get("name")
        if not isinstance(name, str) or not name:
            # Skipping it would drop a gated tool from the policy silently, which
            # is the one outcome this module refuses to produce.
            raise ValueError(
                f"manifests[{index}] declares a gated effect but has no usable "
                f"'name' (got {name!r}), so it cannot be gated"
            )
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


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
        """Require approval for the given patterns; auto-approve everything else.

        With no patterns this auto-approves everything, exactly as
        :meth:`allow_all` does.
        """
        rules = [ApprovalRule(p, ApprovalMode.REQUIRE) for p in patterns]
        rules.append(ApprovalRule("*", ApprovalMode.AUTO))
        return cls(rules)

    @classmethod
    def require_for_effects(
        cls,
        manifests: Iterable[Mapping[str, Any]],
        effects: Iterable[str],
    ) -> "ApprovalPolicy":
        """Require approval for every tool whose manifest declares one of *effects*.

        *manifests* are tool manifests (``{"name": ..., "effects": [...]}``).
        Auto-approves everything else::

            policy = ApprovalPolicy.require_for_effects(
                registry.manifests(), ["fs.write", "network.write"]
            )

        Gating on **declared effects** rather than tool names removes the
        allowlist a host would otherwise maintain: a tool that declares a gated
        effect is gated because of what it declares, not because someone
        remembered to add it.

        **The policy is a snapshot.** It is built from the manifests as they are
        at the call, so a tool registered afterwards is not covered until the
        policy is rebuilt. Rebuild it wherever the tool set changes; this factory
        removes the allowlist, not the need to notice new tools.

        **Never returns a policy that gates nothing.** An effect named in
        *effects* that no manifest declares raises `ValueError` rather than
        quietly matching no tool — a typo (``"fs.wrte"``) is otherwise
        indistinguishable from "nothing needs approval", and the two have
        opposite consequences. Because every requested effect must be one some
        manifest declares, at least one tool always matches, so the empty-policy
        case is unreachable by construction rather than guarded against.

        Where a host genuinely wants to pass a standard vocabulary against a
        registry that may not use all of it, intersect first::

            gated = set(VALID_EFFECTS) & declared_effects(manifests)

        and call :meth:`allow_all` when that comes out empty — which is the same
        decision, made where the caller can see it.

        Raises
        ------
        ValueError
            If *effects* is empty, names an effect no manifest declares, is a
            bare string, or if a manifest declaring a gated effect has no usable
            ``name``.
        """
        manifests = list(manifests)
        gated = _effect_set(effects, "effects")
        if not gated:
            raise ValueError(
                "require_for_effects() needs at least one effect to gate; "
                "use ApprovalPolicy.allow_all() to approve everything"
            )
        observed = declared_effects(manifests)
        unknown = gated - observed
        if unknown:
            raise ValueError(
                f"effect(s) {sorted(unknown)} are declared by no manifest, so "
                f"gating them would approve everything; observed vocabulary: "
                f"{sorted(observed)}"
            )
        return cls.require_for(*tools_with_effects(manifests, gated))
