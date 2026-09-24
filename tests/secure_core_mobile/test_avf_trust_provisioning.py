from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.x509.oid import NameOID

from secure_core_mobile.avf_platform_verifier import (
    _issue_preprovisioned_avf_profile_pin_for_test,
)
from secure_core_mobile.avf_trust_provisioning import (
    activate_preprovisioned_profile,
    prepare_authoritative_profile,
)


SCRIPT = Path("scripts/prepare_secure_core_avf_trust.py")


def _cert_der(name: str, *, ca: bool = True) -> bytes:
    now = datetime.now(timezone.utc)
    key = ed25519.Ed25519PrivateKey.generate()
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(
            x509.BasicConstraints(ca=ca, path_length=None),
            critical=True,
        )
        .sign(key, algorithm=None)
    )
    return cert.public_bytes(serialization.Encoding.DER)


def _write(directory: Path, name: str, data: bytes) -> None:
    (directory / name).write_bytes(data)


def test_profile_receipt_is_order_invariant(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    a = _cert_der("root-a")
    b = _cert_der("root-b")
    _write(first, "10-a.der", a)
    _write(first, "20-b.der", b)
    _write(second, "10-b.der", b)
    _write(second, "20-a.der", a)

    _, left = prepare_authoritative_profile(first, profile_version=7)
    _, right = prepare_authoritative_profile(second, profile_version=7)

    assert left.profile_sha256 == right.profile_sha256
    assert left.anchor_sha256 == right.anchor_sha256
    assert left.receipt_sha256 == right.receipt_sha256
    assert left.authorization_status == "candidate-pin-only"


def test_duplicate_anchor_is_rejected(tmp_path: Path) -> None:
    anchor = _cert_der("duplicate")
    _write(tmp_path, "a.der", anchor)
    _write(tmp_path, "b.der", anchor)

    with pytest.raises(ValueError, match="duplicate"):
        prepare_authoritative_profile(tmp_path)


def test_symlink_anchor_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "root.der"
    target.write_bytes(_cert_der("root"))
    link = tmp_path / "linked.der"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="symlink"):
        prepare_authoritative_profile(tmp_path)


def test_non_ca_anchor_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "leaf.der", _cert_der("leaf", ca=False))

    with pytest.raises(ValueError, match="non-CA"):
        prepare_authoritative_profile(tmp_path)


def test_activation_requires_separately_matching_pin(tmp_path: Path) -> None:
    _write(tmp_path, "root.der", _cert_der("root"))
    store, receipt = prepare_authoritative_profile(tmp_path)

    pin = _issue_preprovisioned_avf_profile_pin_for_test(receipt.profile_sha256)
    profile = activate_preprovisioned_profile(
        store,
        protected_pin=pin,
    )
    assert profile.profile_sha256 == receipt.profile_sha256

    wrong = _issue_preprovisioned_avf_profile_pin_for_test("0" * 64)
    with pytest.raises(ValueError, match="pin mismatch"):
        activate_preprovisioned_profile(
            store,
            protected_pin=wrong,
        )

    with pytest.raises(TypeError, match="protected AVF profile pin"):
        activate_preprovisioned_profile(
            store,
            protected_pin=receipt.profile_sha256,
        )


def test_cli_emits_deterministic_candidate_receipt(tmp_path: Path) -> None:
    anchors = tmp_path / "anchors"
    anchors.mkdir()
    _write(anchors, "root.der", _cert_der("root"))
    one = tmp_path / "one.json"
    two = tmp_path / "two.json"

    for output in (one, two):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--anchors-dir",
                str(anchors),
                "--output",
                str(output),
                "--profile-version",
                "3",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    assert one.read_bytes() == two.read_bytes()
    payload = json.loads(one.read_text(encoding="utf-8"))
    assert payload["profile_version"] == 3
    assert payload["anchor_count"] == 1
    assert payload["authorization_status"] == "candidate-pin-only"
    assert len(payload["profile_sha256"]) == 64
    assert len(payload["receipt_sha256"]) == 64
