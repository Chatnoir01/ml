"""Authenticated transport entry point for the authorization boundary.

Frames must authenticate before RPC decoding/dispatch can reach the
AuthorizationService.
"""

from __future__ import annotations

from .boundary_service import BoundaryService
from .channel import AuthenticatedFrame, SessionVerifier
from .policy import Policy


class AuthenticatedBoundary:
    def __init__(self, *, verifier: SessionVerifier, boundary: BoundaryService):
        self._verifier = verifier
        self._boundary = boundary

    def receive(self, *, frame: AuthenticatedFrame, policy: Policy, payload: bytes):
        envelope = self._verifier.verify_and_decode(frame)
        return self._boundary.dispatch(envelope=envelope, policy=policy, payload=payload)
