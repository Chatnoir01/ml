from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from secure_core_mobile.android_avf_preflight import (
    AvfGuestPreflightState,
    detect_android_runtime,
    run_avf_guest_preflight,
)
from secure_core_mobile.avf_platform_verifier import (
    _issue_preprovisioned_avf_profile_pin_for_test,
)
from secure_core_mobile.platform_evidence import (
    _issue_android_avf_platform_verification,
)


def _valid_ed25519_cose_key() -> bytes:
    public_key = ed25519.Ed25519PrivateKey.generate().public_key()
    x = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return b"\xa4\x01\x01\x03\x27\x20\x06\x21\x58\x20" + x


class _TestPinProvider:
    def load(self):
        return _issue_preprovisioned_avf_profile_pin_for_test("a" * 64)


def test_non_android_runtime_fails_closed() -> None:
    receipt = run_avf_guest_preflight(
        platform="linux",
        exists=lambda path: False,
    )
    assert receipt.state is AvfGuestPreflightState.NON_ANDROID_RUNTIME
    assert receipt.android_runtime_detected is False
    assert receipt.hostile_host_ready is False


def test_android_marker_can_detect_runtime_without_sys_platform_android() -> None:
    assert detect_android_runtime(
        platform="linux",
        exists=lambda path: path == Path("/system/build.prop"),
    ) is True


def test_android_without_secretkeeper_dt_is_not_ready() -> None:
    def missing(path: Path) -> bytes:
        raise FileNotFoundError(path)

    receipt = run_avf_guest_preflight(
        platform="android",
        exists=lambda path: True,
        secretkeeper_reader=missing,
    )
    assert receipt.state is AvfGuestPreflightState.SECRETKEEPER_DT_UNAVAILABLE
    assert receipt.hostile_host_ready is False


def test_valid_secretkeeper_key_yields_secret_free_receipt() -> None:
    encoded = _valid_ed25519_cose_key()
    receipt = run_avf_guest_preflight(
        platform="android",
        secretkeeper_reader=lambda path: encoded,
    )

    assert receipt.state is AvfGuestPreflightState.SECRETKEEPER_KEY_VALID
    assert receipt.secretkeeper_key_profile == "Ed25519"
    assert len(receipt.secretkeeper_key_sha256 or "") == 64
    assert encoded not in receipt.canonical_bytes()
    assert receipt.platform_verified is False
    assert receipt.hostile_host_ready is False


def test_authoritative_platform_token_is_reported_but_not_hostile_ready() -> None:
    encoded = _valid_ed25519_cose_key()
    platform = _issue_android_avf_platform_verification(
        evidence_sha256="b" * 64,
    )
    receipt = run_avf_guest_preflight(
        platform="android",
        secretkeeper_reader=lambda path: encoded,
        platform_verification=platform,
        protected_pin_provider=_TestPinProvider(),
    )

    assert receipt.state is AvfGuestPreflightState.PLATFORM_EVIDENCE_BOUND
    assert receipt.platform_verified is True
    assert receipt.protected_profile_pin_loaded is True
    assert receipt.native_authgraph_available is False
    assert receipt.hostile_host_ready is False
    assert receipt.reason == "platform-verified-native-authgraph-unavailable"


def test_malformed_secretkeeper_key_cannot_advance_preflight() -> None:
    receipt = run_avf_guest_preflight(
        platform="android",
        secretkeeper_reader=lambda path: b"not-a-cose-key",
    )
    assert receipt.state is AvfGuestPreflightState.SECRETKEEPER_DT_UNAVAILABLE
    assert receipt.secretkeeper_key_sha256 is None
    assert receipt.hostile_host_ready is False
