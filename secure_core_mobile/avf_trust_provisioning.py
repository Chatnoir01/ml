"""Offline preparation of an authoritative AVF trust profile.

This module intentionally separates *preparation* from *authorization*.

Preparation:
- reads an explicit directory of DER X.509 trust anchors;
- rejects symlinks, duplicate anchors, malformed certificates and oversized files;
- computes the same canonical profile SHA-256 enforced by the runtime verifier;
- emits a deterministic, secret-free receipt suitable for review.

Authorization:
- still requires the resulting profile SHA-256 to be provisioned separately
  inside the protected deployment boundary. A receipt or anchor directory by
  itself never creates PLATFORM_VERIFIED evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes

from .avf_platform_verifier import (
    AuthoritativeAvfTrustProfile,
    authoritative_profile_sha256,
)
from .cert_chain import CertificateTrustStore


MAX_ANCHOR_BYTES = 1024 * 1024
PROVISIONING_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AvfTrustProvisioningReceipt:
    schema_version: int
    profile_version: int
    anchor_count: int
    anchor_sha256: tuple[str, ...]
    profile_sha256: str
    authorization_status: str = "candidate-pin-only"

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            asdict(self),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

    @property
    def receipt_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _read_anchor(path: Path) -> bytes:
    if path.is_symlink():
        raise ValueError(f"symlink trust anchor rejected: {path.name}")
    if not path.is_file():
        raise ValueError(f"non-file trust anchor rejected: {path.name}")
    if path.suffix.lower() != ".der":
        raise ValueError(f"trust anchor must use .der: {path.name}")

    size = path.stat().st_size
    if size <= 0:
        raise ValueError(f"empty trust anchor rejected: {path.name}")
    if size > MAX_ANCHOR_BYTES:
        raise ValueError(f"trust anchor exceeds size limit: {path.name}")

    data = path.read_bytes()
    try:
        cert = x509.load_der_x509_certificate(data)
    except ValueError as exc:
        raise ValueError(f"malformed DER trust anchor: {path.name}") from exc

    try:
        constraints = cert.extensions.get_extension_for_class(
            x509.BasicConstraints
        ).value
    except x509.ExtensionNotFound as exc:
        raise ValueError(f"trust anchor lacks CA basic constraints: {path.name}") from exc
    if not constraints.ca:
        raise ValueError(f"non-CA trust anchor rejected: {path.name}")

    return data


def load_anchor_directory(directory: Path | str) -> CertificateTrustStore:
    root = Path(directory)
    if root.is_symlink():
        raise ValueError("trust-anchor directory symlink rejected")
    if not root.is_dir():
        raise ValueError("trust-anchor directory is unavailable")

    entries = sorted(root.iterdir(), key=lambda path: path.name)
    if not entries:
        raise ValueError("trust-anchor directory is empty")

    anchors = tuple(_read_anchor(path) for path in entries)
    fingerprints = [
        x509.load_der_x509_certificate(anchor).fingerprint(hashes.SHA256())
        for anchor in anchors
    ]
    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError("duplicate trust anchor rejected")

    return CertificateTrustStore(anchors)


def prepare_authoritative_profile(
    directory: Path | str,
    *,
    profile_version: int = 1,
) -> tuple[CertificateTrustStore, AvfTrustProvisioningReceipt]:
    store = load_anchor_directory(directory)
    profile_sha = authoritative_profile_sha256(
        store,
        profile_version=profile_version,
    )
    receipt = AvfTrustProvisioningReceipt(
        schema_version=PROVISIONING_SCHEMA_VERSION,
        profile_version=profile_version,
        anchor_count=len(store.anchors_der),
        anchor_sha256=tuple(sorted(
            hashlib.sha256(anchor).hexdigest()
            for anchor in store.anchors_der
        )),
        profile_sha256=profile_sha,
    )
    return store, receipt


def activate_preprovisioned_profile(
    store: CertificateTrustStore,
    *,
    expected_profile_sha256: str,
    profile_version: int = 1,
) -> AuthoritativeAvfTrustProfile:
    """Activate only against a pin supplied by a separate protected channel."""
    return AuthoritativeAvfTrustProfile(
        certificate_store=store,
        expected_profile_sha256=expected_profile_sha256,
        profile_version=profile_version,
    )
