from __future__ import annotations

import ctypes

import pytest

import secure_core_mobile.android_native_bridge as bridge_mod
from secure_core_mobile.android_native_bridge import (
    AndroidNativeBridge,
    AndroidNativeBridgeCallError,
    AndroidNativeBridgeUnavailable,
    NativeBridgeState,
    load_android_native_bridge,
)


class _FakeFunction:
    def __init__(self, implementation):
        self._implementation = implementation
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self._implementation(*args)


class _FakeLibrary:
    def __init__(
        self,
        *,
        certificates: tuple[bytes, ...] = (b"leaf", b"issuer"),
        attestation_status: int = 0,
        pin_status: int = 0,
        pin: bytes = b"p" * 32,
    ) -> None:
        self.certificates = certificates
        self.attestation_status = attestation_status
        self.pin_status = pin_status
        self.pin = pin
        self.freed_chain = False
        self._certificate_buffers = []
        self._certificate_array = None

        self.scm_avf_request_attestation = _FakeFunction(
            self._request_attestation
        )
        self.scm_avf_free_certificate_chain = _FakeFunction(
            self._free_certificate_chain
        )
        self.scm_avf_load_preprovisioned_profile_pin = _FakeFunction(
            self._load_pin
        )
        self.scm_secretkeeper_process_protected_packet = _FakeFunction(
            lambda *args: 0
        )
        self.scm_secretkeeper_free_packet = _FakeFunction(
            lambda *args: None
        )

    def _request_attestation(self, challenge, challenge_size, chain_pointer):
        if self.attestation_status != 0:
            return self.attestation_status

        buffers = []
        array = (
            bridge_mod._ScmAvfCertificate * len(self.certificates)
        )()
        for index, encoded in enumerate(self.certificates):
            buffer = (ctypes.c_uint8 * len(encoded)).from_buffer_copy(encoded)
            buffers.append(buffer)
            array[index].data = ctypes.cast(
                buffer,
                ctypes.POINTER(ctypes.c_uint8),
            )
            array[index].size = len(encoded)

        chain = ctypes.cast(
            chain_pointer,
            ctypes.POINTER(bridge_mod._ScmAvfCertificateChain),
        ).contents
        chain.certificates = ctypes.cast(
            array,
            ctypes.POINTER(bridge_mod._ScmAvfCertificate),
        )
        chain.certificate_count = len(self.certificates)

        self._certificate_buffers = buffers
        self._certificate_array = array
        return 0

    def _free_certificate_chain(self, chain_pointer):
        self.freed_chain = True

    def _load_pin(self, out_pin, out_size):
        if self.pin_status != 0:
            return self.pin_status
        assert out_size == 32
        for index, value in enumerate(self.pin):
            out_pin[index] = value
        return 0


def test_native_bridge_refuses_non_android_runtime_before_loading() -> None:
    called = False

    def loader(path: str):
        nonlocal called
        called = True
        return _FakeLibrary()

    with pytest.raises(AndroidNativeBridgeUnavailable, match="outside Android"):
        load_android_native_bridge(
            "/data/local/tmp/libsecure_core.so",
            platform="linux",
            loader=loader,
        )
    assert called is False


def test_native_bridge_requires_absolute_path() -> None:
    with pytest.raises(ValueError, match="absolute"):
        load_android_native_bridge(
            "libsecure_core.so",
            platform="android",
            loader=lambda path: _FakeLibrary(),
        )


def test_missing_required_symbol_fails_closed() -> None:
    library = _FakeLibrary()
    del library.scm_secretkeeper_free_packet

    with pytest.raises(AndroidNativeBridgeUnavailable, match="missing required"):
        load_android_native_bridge(
            "/system/lib64/libsecure_core.so",
            platform="android",
            loader=lambda path: library,
        )


def test_loaded_bridge_is_explicitly_unverified() -> None:
    bridge = load_android_native_bridge(
        "/system/lib64/libsecure_core.so",
        platform="android",
        loader=lambda path: _FakeLibrary(),
    )
    assert bridge.probe.state is NativeBridgeState.LOADED_UNVERIFIED
    assert bridge.probe.trusted_platform_boundary is False


def test_attestation_chain_is_copied_and_native_memory_is_freed() -> None:
    library = _FakeLibrary(certificates=(b"leaf-der", b"issuer-der"))
    bridge = AndroidNativeBridge(
        library,
        source_path="/system/lib64/libsecure_core.so",
    )

    result = bridge.request_avf_attestation(b"fresh-challenge")

    assert result == (b"leaf-der", b"issuer-der")
    assert library.freed_chain is True


def test_native_attestation_error_status_is_preserved() -> None:
    bridge = AndroidNativeBridge(
        _FakeLibrary(attestation_status=-20003),
        source_path="/system/lib64/libsecure_core.so",
    )
    with pytest.raises(AndroidNativeBridgeCallError) as exc:
        bridge.request_avf_attestation(b"fresh")
    assert exc.value.status == -20003
    assert exc.value.operation == "AVF attestation"


@pytest.mark.parametrize("challenge", [b"", b"x" * 65])
def test_invalid_challenge_is_rejected_before_native_call(challenge: bytes) -> None:
    bridge = AndroidNativeBridge(
        _FakeLibrary(),
        source_path="/system/lib64/libsecure_core.so",
    )
    with pytest.raises(ValueError, match="1..64"):
        bridge.request_avf_attestation(challenge)


def test_profile_pin_bytes_are_transport_data_not_trust_token() -> None:
    raw_pin = bytes(range(32))
    bridge = AndroidNativeBridge(
        _FakeLibrary(pin=raw_pin),
        source_path="/system/lib64/libsecure_core.so",
    )

    result = bridge.load_preprovisioned_profile_pin_bytes()

    assert result == raw_pin
    assert isinstance(result, bytes)


def test_profile_pin_native_error_is_preserved() -> None:
    bridge = AndroidNativeBridge(
        _FakeLibrary(pin_status=-21002),
        source_path="/system/lib64/libsecure_core.so",
    )
    with pytest.raises(AndroidNativeBridgeCallError) as exc:
        bridge.load_preprovisioned_profile_pin_bytes()
    assert exc.value.status == -21002
    assert exc.value.operation == "AVF profile pin load"
