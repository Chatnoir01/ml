from __future__ import annotations

import re
from pathlib import Path


RUST = Path("secure_core_mobile/android_native/secretkeeper_verified_session.rs")
BP = Path("secure_core_mobile/android_native/Android.bp")


def test_verified_sk_session_requires_expected_secretkeeper_identity() -> None:
    source = RUST.read_text(encoding="utf-8")

    assert "expected_sk_key_cbor" in source
    assert "CoseKey::from_slice(expected_sk_key_cbor)" in source
    assert "use explicitkeydice::OwnedDiceArtifactsWithExplicitKey;" in source
    assert re.search(
        r"SkSession::new\(\s*sk,\s*dice,\s*Some\(expected_sk_key\)\s*\)",
        source,
        re.MULTILINE,
    )
    assert "SkSession::new(sk, dice, None)" not in source


def test_verified_sk_session_does_not_expose_aes_session_keys() -> None:
    source = RUST.read_text(encoding="utf-8")

    assert "pub fn session_id" in source
    assert "pub fn encryption_key" not in source
    assert "pub fn decryption_key" not in source
    assert ".encryption_key()" not in source
    assert ".decryption_key()" not in source


def test_verified_sk_session_rejects_empty_identity_and_request_before_binder() -> None:
    source = RUST.read_text(encoding="utf-8")

    assert "EmptyExpectedIdentity" in source
    assert "expected_sk_key_cbor.is_empty()" in source
    assert "EmptyRequest" in source
    assert "request.is_empty()" in source


def test_verified_sk_session_soong_module_pins_aosp_dependencies() -> None:
    build = BP.read_text(encoding="utf-8")

    assert 'name: "libsecure_core_secretkeeper_verified_session"' in build
    assert 'defaults: ["secretkeeper_use_latest_hal_aidl_rust"]' in build
    for dependency in (
        "android.hardware.security.secretkeeper-V1-rust",
        "libbinder_rs",
        "libcoset",
        "libexplicitkeydice",
        "libsecretkeeper_client",
    ):
        assert f'"{dependency}"' in build
