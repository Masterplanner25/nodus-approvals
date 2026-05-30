from nodus_approvals import ApprovalMode, ApprovalPolicy, ApprovalRule


def test_allow_all_resolves_auto():
    policy = ApprovalPolicy.allow_all()
    rule = policy.resolve("exec.bash")
    assert rule.mode == ApprovalMode.AUTO


def test_deny_all_resolves_deny():
    policy = ApprovalPolicy.deny_all()
    rule = policy.resolve("anything")
    assert rule.mode == ApprovalMode.DENY


def test_require_for_matches_pattern():
    policy = ApprovalPolicy.require_for("exec.*")
    rule = policy.resolve("exec.bash")
    assert rule.mode == ApprovalMode.REQUIRE


def test_require_for_fallback_auto():
    policy = ApprovalPolicy.require_for("exec.*")
    rule = policy.resolve("memory.read")
    assert rule.mode == ApprovalMode.AUTO


def test_first_match_wins():
    policy = ApprovalPolicy([
        ApprovalRule("exec.*", ApprovalMode.REQUIRE),
        ApprovalRule("*", ApprovalMode.AUTO),
    ])
    assert policy.resolve("exec.bash").mode == ApprovalMode.REQUIRE
    assert policy.resolve("other").mode == ApprovalMode.AUTO


def test_no_match_defaults_to_require():
    policy = ApprovalPolicy([])   # empty rules
    rule = policy.resolve("anything")
    assert rule.mode == ApprovalMode.REQUIRE


def test_approver_ids_preserved():
    rule = ApprovalRule("admin.*", ApprovalMode.REQUIRE, approver_ids=["ops"])
    policy = ApprovalPolicy([rule])
    resolved = policy.resolve("admin.promote")
    assert "ops" in resolved.approver_ids


def test_fnmatch_wildcard():
    policy = ApprovalPolicy([ApprovalRule("send.*", ApprovalMode.DENY)])
    assert policy.resolve("send.dm").mode == ApprovalMode.DENY
    assert policy.resolve("receive.dm").mode == ApprovalMode.REQUIRE  # fallback
