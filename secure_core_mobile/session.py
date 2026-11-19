"""Session establishment with explicit trust provenance.

Development sessions can exercise protocol semantics but are never promoted to
trusted-boundary sessions. Future pVM establishment must supply qualifying
BoundaryEvidence and derive key material inside that boundary.
"""

from __future__ import annotations
from dataclasses import dataclass
import secrets

from .channel import SessionVerifier
from .hostile_boundary import BoundaryEvidence


@dataclass(frozen=True)
class SessionContext:
    session_id: str
    verifier: SessionVerifier
    trusted_boundary: bool
    provenance: str


def establish_development_session() -> tuple[SessionContext, bytes]:
    key = secrets.token_bytes(32)
    session_id = secrets.token_hex(16)
    return (
        SessionContext(
            session_id=session_id,
            verifier=SessionVerifier(session_id=session_id, key=key),
            trusted_boundary=False,
            provenance="development-process-random",
        ),
        key,
    )


def establish_boundary_session(*, boundary: BoundaryEvidence, derived_key: bytes) -> SessionContext:
    if not boundary.qualifies_for_hostile_host_experiment:
        raise ValueError("boundary does not qualify for trusted session establishment")
    if len(derived_key) < 32:
        raise ValueError("derived session key too short")
    # This constructor records the required provenance contract. It does not
    # claim the supplied key was actually derived inside pVM; the Android/pVM
    # adapter must provide evidence for that fact.
    session_id = secrets.token_hex(16)
    return SessionContext(
        session_id=session_id,
        verifier=SessionVerifier(session_id=session_id, key=derived_key),
        trusted_boundary=True,
        provenance=f"qualified-boundary:{boundary.boundary_id}",
    )
