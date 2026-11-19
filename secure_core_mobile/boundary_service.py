"""Protected-boundary RPC entry point.

There is intentionally no public sign()/decrypt() method. All operations cross
the AuthorizationService.
"""

from __future__ import annotations

from .authorization import AuthorizationResult, AuthorizationService
from .policy import AuthorizationRequest, Policy
from .rpc import RpcEnvelope, validate_envelope


class BoundaryService:
    def __init__(self, authorization: AuthorizationService):
        self._authorization = authorization

    def dispatch(self, *, envelope: RpcEnvelope, policy: Policy, payload: bytes) -> AuthorizationResult:
        validate_envelope(envelope, payload=payload)
        request = AuthorizationRequest(
            operation=envelope.operation,
            key_handle=envelope.key_handle,
            policy_version=envelope.policy_version,
            nonce=envelope.nonce,
        )
        return self._authorization.execute(
            request=request,
            policy=policy,
            payload=payload,
        )
