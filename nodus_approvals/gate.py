"""ApprovalGate — check, approve, deny, and poll approval requests."""
from __future__ import annotations

from .policy import ApprovalMode, ApprovalPolicy
from .request import ApprovalRequest, ApprovalResult
from .store import ApprovalStore


class ApprovalGate:
    """Manage the full lifecycle of approval requests.

    Usage::

        gate = ApprovalGate(
            policy=ApprovalPolicy.require_for("exec.*"),
            store=InMemoryApprovalStore(),
        )

        # Check — returns None if human approval is required
        result = gate.check("exec.bash", requester_id="agent-1", context={"cmd": "ls"})
        if result is None:
            request_id = gate.last_request_id  # or look up via store.pending()
            # ... wait for human to call gate.approve(request_id, "ops-user") ...
        elif result.approved:
            # auto-approved by policy
            ...
    """

    def __init__(self, policy: ApprovalPolicy, store: ApprovalStore) -> None:
        self._policy = policy
        self._store = store
        self._last_request_id: str | None = None

    @property
    def last_request_id(self) -> str | None:
        """ID of the most recently created pending request (convenience accessor)."""
        return self._last_request_id

    def check(
        self,
        action: str,
        requester_id: str,
        context: dict | None = None,
    ) -> ApprovalResult | None:
        """Evaluate *action* against the policy.

        Returns
        -------
        ApprovalResult
            Immediately when mode is ``AUTO`` or ``DENY``.
        None
            When mode is ``REQUIRE`` or ``PAIRING``.  A pending
            ``ApprovalRequest`` is created and saved to the store.
            Call ``approve()`` or ``deny()`` with the request ID to resolve it.
        """
        rule = self._policy.resolve(action)

        if rule.mode == ApprovalMode.AUTO:
            return ApprovalResult(
                request_id="auto",
                approved=True,
                approver_id=None,
                reason="policy:auto",
            )

        if rule.mode == ApprovalMode.DENY:
            return ApprovalResult(
                request_id="deny",
                approved=False,
                approver_id=None,
                reason="policy:deny",
            )

        # REQUIRE or PAIRING — create a pending request
        request = ApprovalRequest.create(
            action=action,
            requester_id=requester_id,
            context=context,
        )
        self._store.save(request)
        self._last_request_id = request.id
        return None

    def approve(
        self,
        request_id: str,
        approver_id: str,
        reason: str | None = None,
    ) -> ApprovalResult:
        """Approve a pending request."""
        result = ApprovalResult(
            request_id=request_id,
            approved=True,
            approver_id=approver_id,
            reason=reason,
        )
        self._store.resolve(request_id, result)
        return result

    def deny(
        self,
        request_id: str,
        approver_id: str,
        reason: str | None = None,
    ) -> ApprovalResult:
        """Deny a pending request."""
        result = ApprovalResult(
            request_id=request_id,
            approved=False,
            approver_id=approver_id,
            reason=reason,
        )
        self._store.resolve(request_id, result)
        return result

    def poll(self, request_id: str) -> ApprovalResult | None:
        """Return the result for *request_id*, or None if still pending."""
        return self._store.get_result(request_id)
