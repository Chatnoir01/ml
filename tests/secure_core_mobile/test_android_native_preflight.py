from __future__ import annotations

import ctypes
import hashlib

from secure_core_mobile.android_native_preflight import (
    AndroidNativePreflightState,
    run_android_native_preflight,
)
import secure_core_mobile.android_native_bridge as bridge_mod


class _FakeFunction:
    def __init__(self, impl):
        self.impl = impl
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.impl(*args)


class _Library:
    def __init__(
        self,
        *,
        pin_status: int = -21002,
        pin: bytes = b"p" * 32,
        attestation_status: int = 0,
        certificates: tuple[bytes, ...] = (b"leaf-secret", b"issuer-secret"),
    ) -> None:
        self.pin_status = pin_status
        self.pin = pin
        self.attestation_status = attestation_status
        self.certificates = certificates
        self.buffers = []
        self.array = None

        self.scm_avf_request_attestation = _FakeFunction(self._attest)
        self.scm_avf_free_certificate_chain = _FakeFunction(lambda ptr: None)
        self.scm_avf_load_preprovisioned_profile_pin = _FakeFunction(self._pin)
        self.scm_secretkeeper_process_protected_packet = _FakeFunction(
            lambda *args: 0
        )
        self.scm_secretkeeper_free_packet = _FakeFunction(lambda *args: None)

    def _pin(self, out_pin, size):
        if self.pin_status != 0:
            return self.pin_status
        for index, value in enumerate(self.pin):
            out_pin[index] = value
        return 0

    def _attest(self, challenge, challenge_size, chain_pointer):
        if self.attestation_status != 0:
            return self.attestation_status

        array = (
            bridge_mod._ScmAvfCertificate * len(self.certificates)
        )()
        buffers = []
        for index, certificate in enumerate(self.certificates):
            buffer = (
                ctypes.c_uint8 * len(certificate)
            ).from_buffer_copy(certificate)
            buffers.append(buffer)
            array[index].data = ctypes.cast(
                buffer,
                ctypes.POINTER(ctypes.c_uint8),
            )
            array[index].size = len(certificate)

        chain = ctypes.cast(
            chain_pointer,
            ctypes.POINTER(bridge_mod._ScmAvfCertificateChain),
        ).contents
        chain.certificates = ctypes.cast(
            array,
            ctypes.POINTER(bridge_mod._ScmAvfCertificate),
        )
        chain.certificate_count = len(self.certificates)

        self.buffers = buffers
        self.array = array
        return 0


def test_non_android_preflight_does_not_load_library() -> None:
    called = False

    def loader(path: str):
        nonlocal called
        called = True
        return _Library()

    receipt = run_android_native_preflight(
        bridge_path="/system/lib64/libsecure_core_avf_attestation_bridge.so",
        platform="linux",
        loader=loader,
    )

    assert receipt.state is AndroidNativePreflightState.NON_ANDROID_RUNTIME
    assert receipt.bridge_loaded is False
    assert receipt.trusted_platform_boundary is False
    assert called is False


def test_loaded_bridge_without_pin_remains_unverified() -> None:
    receipt = run_android_native_preflight(
        bridge_path="/system/lib64/libsecure_core_avf_attestation_bridge.so",
        platform="android",
        loader=lambda path: _Library(),
    )

    assert receipt.state is AndroidNativePreflightState.BRIDGE_LOADED_UNVERIFIED
    assert receipt.bridge_loaded is True
    assert receipt.profile_pin_present is False
    assert receipt.profile_pin_native_status == -21002
    assert receipt.trusted_platform_boundary is False


def test_profile_pin_presence_is_hashed_and_not_promoted() -> None:
    pin = bytes(range(32))
    receipt = run_android_native_preflight(
        bridge_path="/system/lib64/libsecure_core_avf_attestation_bridge.so",
        platform="android",
        loader=lambda path: _Library(pin_status=0, pin=pin),
    )

    assert (
        receipt.state
        is AndroidNativePreflightState.PROFILE_PIN_PRESENT_UNVERIFIED
    )
    assert receipt.profile_pin_sha256 == hashlib.sha256(pin).hexdigest()
    assert pin not in receipt.canonical_bytes()
    assert receipt.trusted_platform_boundary is False


def test_attestation_observation_records_only_digest_metadata() -> None:
    challenge = b"fresh-third-party-challenge"
    certificates = (b"leaf-private-test", b"issuer-private-test")
    receipt = run_android_native_preflight(
        bridge_path="/system/lib64/libsecure_core_avf_attestation_bridge.so",
        platform="android",
        challenge=challenge,
        loader=lambda path: _Library(
            pin_status=0,
            certificates=certificates,
        ),
    )

    assert (
        receipt.state
        is AndroidNativePreflightState.ATTESTATION_OBSERVED_UNVERIFIED
    )
    assert receipt.attestation_observed is True
    assert receipt.certificate_count == 2
    assert len(receipt.certificate_chain_sha256 or "") == 64
    assert receipt.challenge_sha256 == hashlib.sha256(challenge).hexdigest()
    assert challenge not in receipt.canonical_bytes()
    for certificate in certificates:
        assert certificate not in receipt.canonical_bytes()
    assert receipt.trusted_platform_boundary is False


def test_native_attestation_failure_never_becomes_trusted() -> None:
    receipt = run_android_native_preflight(
        bridge_path="/system/lib64/libsecure_core_avf_attestation_bridge.so",
        platform="android",
        challenge=b"fresh",
        loader=lambda path: _Library(attestation_status=-20003),
    )

    assert receipt.attestation_observed is False
    assert receipt.attestation_native_status == -20003
    assert receipt.trusted_platform_boundary is False
