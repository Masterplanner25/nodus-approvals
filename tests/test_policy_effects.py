"""ApprovalPolicy.require_for_effects — gating on declared effects, not tool names.

The property under test throughout is that this factory **never produces a policy
that gates nothing**. Every case below is either a tool being gated because of
what it declares, or a refusal that stops a silent auto-approve-everything.
"""
import pytest

from nodus_approvals import (
    ApprovalMode,
    ApprovalPolicy,
    declared_effects,
    tools_with_effects,
)

MANIFESTS = [
    {"name": "fs.read_file", "effects": ["fs.read"]},
    {"name": "fs.write_file", "effects": ["fs.read", "fs.write"]},
    {"name": "net.fetch", "effects": ["network.read"]},
    {"name": "net.post", "effects": ["network.write"]},
    {"name": "math.add", "effects": []},
    {"name": "clock.now"},  # no "effects" key at all
]


# ── the gate itself ───────────────────────────────────────────────────────────

def test_tool_declaring_a_gated_effect_requires_approval():
    policy = ApprovalPolicy.require_for_effects(MANIFESTS, ["fs.write"])
    assert policy.resolve("fs.write_file").mode == ApprovalMode.REQUIRE


def test_tool_declaring_none_of_them_is_auto():
    policy = ApprovalPolicy.require_for_effects(MANIFESTS, ["fs.write"])
    for name in ("fs.read_file", "net.fetch", "math.add", "clock.now"):
        assert policy.resolve(name).mode == ApprovalMode.AUTO, name


def test_several_effects_gate_the_union():
    policy = ApprovalPolicy.require_for_effects(MANIFESTS, ["fs.write", "network.write"])
    assert policy.resolve("fs.write_file").mode == ApprovalMode.REQUIRE
    assert policy.resolve("net.post").mode == ApprovalMode.REQUIRE
    assert policy.resolve("net.fetch").mode == ApprovalMode.AUTO


def test_a_tool_registered_later_is_gated_by_the_same_call():
    """The point of the factory: no allowlist to extend.

    Rebuilding the policy over the new manifest list gates the new tool without
    anyone naming it — which is also the reminder that the policy is a snapshot
    and must be rebuilt.
    """
    added = MANIFESTS + [{"name": "db.truncate", "effects": ["fs.write"]}]
    policy = ApprovalPolicy.require_for_effects(added, ["fs.write"])
    assert policy.resolve("db.truncate").mode == ApprovalMode.REQUIRE


def test_the_effect_vocabulary_is_opaque():
    """Works with the coarse nodus_lang_schema vocabulary as well as a fine one."""
    coarse = [
        {"name": "writer", "effects": ["filesystem", "writes_state"]},
        {"name": "reader", "effects": ["reads_state"]},
    ]
    policy = ApprovalPolicy.require_for_effects(coarse, ["filesystem"])
    assert policy.resolve("writer").mode == ApprovalMode.REQUIRE
    assert policy.resolve("reader").mode == ApprovalMode.AUTO


# ── the refusals: every one of these would otherwise gate nothing ─────────────

def test_an_effect_no_manifest_declares_is_refused():
    with pytest.raises(ValueError) as err:
        ApprovalPolicy.require_for_effects(MANIFESTS, ["fs.wrte"])
    assert "fs.wrte" in str(err.value)
    assert "fs.write" in str(err.value)  # the observed vocabulary is reported


def test_one_bad_effect_among_good_ones_is_refused():
    """A typo must not be masked by a sibling that happens to match."""
    with pytest.raises(ValueError):
        ApprovalPolicy.require_for_effects(MANIFESTS, ["fs.write", "fs.wrte"])


def test_no_effects_at_all_is_refused():
    with pytest.raises(ValueError) as err:
        ApprovalPolicy.require_for_effects(MANIFESTS, [])
    assert "allow_all" in str(err.value)


def test_a_bare_string_is_refused_not_iterated():
    """frozenset("fs.write") is eleven characters and would match nothing."""
    with pytest.raises(ValueError) as err:
        ApprovalPolicy.require_for_effects(MANIFESTS, "fs.write")
    assert "single string" in str(err.value)


def test_a_gated_manifest_with_no_name_is_refused():
    broken = MANIFESTS + [{"effects": ["fs.write"]}]
    with pytest.raises(ValueError) as err:
        ApprovalPolicy.require_for_effects(broken, ["fs.write"])
    assert "name" in str(err.value)


def test_an_unnamed_manifest_that_is_not_gated_is_ignored():
    """Only a tool the policy would have to gate needs a name."""
    tolerated = MANIFESTS + [{"effects": ["fs.read"]}]
    policy = ApprovalPolicy.require_for_effects(tolerated, ["fs.write"])
    assert policy.resolve("fs.write_file").mode == ApprovalMode.REQUIRE


# ── helpers ───────────────────────────────────────────────────────────────────

def test_declared_effects_reports_the_vocabulary():
    assert declared_effects(MANIFESTS) == frozenset(
        {"fs.read", "fs.write", "network.read", "network.write"}
    )


def test_intersecting_first_is_the_escape_hatch():
    """The documented way to pass a standard vocabulary to a partial registry."""
    read_only = [{"name": "fs.read_file", "effects": ["fs.read"]}]
    vocabulary = {"fs.read", "fs.write", "network.write"}

    with pytest.raises(ValueError):
        ApprovalPolicy.require_for_effects(read_only, vocabulary)

    gated = vocabulary & declared_effects(read_only)
    policy = ApprovalPolicy.require_for_effects(read_only, gated)
    assert policy.resolve("fs.read_file").mode == ApprovalMode.REQUIRE


def test_tools_with_effects_keeps_manifest_order_and_dedupes():
    repeated = [
        {"name": "b", "effects": ["fs.write"]},
        {"name": "a", "effects": ["fs.write"]},
        {"name": "b", "effects": ["network.write"]},
    ]
    assert tools_with_effects(repeated, ["fs.write", "network.write"]) == ["b", "a"]


def test_a_generator_of_manifests_is_consumed_once():
    """The factory reads the manifests twice; a generator must still work."""
    policy = ApprovalPolicy.require_for_effects((m for m in MANIFESTS), ["fs.write"])
    assert policy.resolve("fs.write_file").mode == ApprovalMode.REQUIRE
