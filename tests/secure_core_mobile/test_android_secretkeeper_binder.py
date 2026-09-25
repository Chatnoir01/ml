from __future__ import annotations

import ctypes
from pathlib import Path

import pytest

import secure_core_mobile.android_secretkeeper_binder as binder_mod
from secure_core_mobile.android_native_bridge import (
    AndroidNativeBridgeCallError,
    AndroidNativeBridgeUnavailable,
    NativeBridgeState,
)
from secure_core_mobile.android_secretkeeper_binder import (
    AndroidSecretkeeperBinderBridge,
    load_secretkeeper_binder_bridge,
    load_system_secretkeeper_binder_bridge,
)


SOURCE = Path(
    "secure_core_mobile/android_native/secretkeeper_binder_bridge.rs"
)
ANDROID_BP = Path("secure_core_mobile/android_native/Android.bp")


class _FakeFunction:
    def __init__(self, impl):
        self.impl = impl
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.impl(*args)


class _FakeBinderLibrary:
    def __init__(
        self,
        *,
        response: bytes = b"protected-response",
        status: int = 0,
        probe_status: int = 0,
    ) -> None:
        self.response = response
        self.status = status
        self.probe_status = probe_status
        self.freed = False
        self.buffer = None

        self.scm_secretkeeper_binder_probe_service = _FakeFunction(
            lambda: self.probe_status
        )
        self.scm_secretkeeper_binder_process = _FakeFunction(self._process)
        self.scm_secretkeeper_binder_free_packet = _FakeFunction(self._free)

    def _process(self, request, request_size, response_pointer):
        if self.status != 0:
            return self.status

        buffer = (
            ctypes.c_uint8 * len(self.response)
        ).from_buffer_copy(self.response)
        packet = ctypes.cast(
            response_pointer,
            ctypes.POINTER(binder_mod._ScmSecretkeeperBinderPacket),
        ).contents
        packet.data = ctypes.cast(
            buffer,
            ctypes.POINTER(ctypes.c_uint8),
        )
        packet.size = len(self.response)
        self.buffer = buffer
        return 0

    def _free(self, packet_pointer):
        self.freed = True


def test_generic_binder_loader_is_disabled_for_vm_payloads() -> None:
    with pytest.raises(AndroidNativeBridgeUnavailable, match="system-side only"):
        load_secretkeeper_binder_bridge(
            "/system/lib64/libsecure_core_secretkeeper_binder_bridge.so",
            platform="android",
        )


def test_secretkeeper_binder_bridge_refuses_non_android_runtime() -> None:
    called = False

    def loader(path: str):
        nonlocal called
        called = True
        return _FakeBinderLibrary()

    with pytest.raises(AndroidNativeBridgeUnavailable, match="outside Android"):
        load_system_secretkeeper_binder_bridge(
            "/system/lib64/libsecure_core_secretkeeper_binder_bridge.so",
            platform="linux",
            loader=loader,
        )
    assert called is False


def test_secretkeeper_binder_bridge_requires_all_symbols() -> None:
    library = _FakeBinderLibrary()
    del library.scm_secretkeeper_binder_free_packet

    with pytest.raises(AndroidNativeBridgeUnavailable, match="missing required"):
        load_system_secretkeeper_binder_bridge(
            "/system/lib64/libsecure_core_secretkeeper_binder_bridge.so",
            platform="android",
            loader=lambda path: library,
        )


def test_loaded_binder_bridge_remains_unverified() -> None:
    bridge = load_system_secretkeeper_binder_bridge(
        "/system/lib64/libsecure_core_secretkeeper_binder_bridge.so",
        platform="android",
        loader=lambda path: _FakeBinderLibrary(),
    )
    assert bridge.probe.state is NativeBridgeState.LOADED_UNVERIFIED
    assert bridge.probe.trusted_platform_boundary is False
    assert "authgraph-unverified" in bridge.probe.reason


def test_binder_service_probe_reports_reachability_without_authgraph() -> None:
    present = AndroidSecretkeeperBinderBridge(
        _FakeBinderLibrary(probe_status=0),
        source_path="/system/lib64/libsecure_core_secretkeeper_binder_bridge.so",
    )
    absent = AndroidSecretkeeperBinderBridge(
        _FakeBinderLibrary(probe_status=-23002),
        source_path="/system/lib64/libsecure_core_secretkeeper_binder_bridge.so",
    )

    assert present.probe_service() is True
    assert absent.probe_service() is False
    assert present.probe.trusted_platform_boundary is False
    assert absent.probe.trusted_platform_boundary is False


def test_protected_packet_response_is_copied_and_freed() -> None:
    library = _FakeBinderLibrary(response=b"opaque-protected-response")
    bridge = AndroidSecretkeeperBinderBridge(
        library,
        source_path="/system/lib64/libsecure_core_secretkeeper_binder_bridge.so",
    )

    response = bridge.process_protected_packet(b"opaque-protected-request")

    assert response == b"opaque-protected-response"
    assert library.freed is True


def test_binder_native_status_is_preserved() -> None:
    bridge = AndroidSecretkeeperBinderBridge(
        _FakeBinderLibrary(status=-23002),
        source_path="/system/lib64/libsecure_core_secretkeeper_binder_bridge.so",
    )
    with pytest.raises(AndroidNativeBridgeCallError) as exc:
        bridge.process_protected_packet(b"opaque")
    assert exc.value.status == -23002
    assert "protected-packet" in exc.value.operation


@pytest.mark.parametrize("packet", [b"", b"x" * (1024 * 1024 + 1)])
def test_invalid_protected_packet_is_rejected_before_binder(
    packet: bytes,
) -> None:
    bridge = AndroidSecretkeeperBinderBridge(
        _FakeBinderLibrary(),
        source_path="/system/lib64/libsecure_core_secretkeeper_binder_bridge.so",
    )
    with pytest.raises(ValueError):
        bridge.process_protected_packet(packet)


def test_rust_bridge_uses_only_protected_binder_transport_contract() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "binder::get_interface" in source
    assert (
        "android.hardware.security.secretkeeper.ISecretkeeper/default"
        in source
    )
    assert "processSecretManagementRequest" in source
    assert "scm_secretkeeper_binder_probe_service" in source

    # AuthGraph/crypto ownership remains outside this transport-only bridge.
    forbidden = (
        "getAuthGraphKe",
        "SkSession",
        "StoreSecret",
        "GetSecret",
        "encryption_key",
        "decryption_key",
    )
    for marker in forbidden:
        assert marker not in source


def test_soong_builds_secretkeeper_binder_as_rust_ffi_shared() -> None:
    android_bp = ANDROID_BP.read_text(encoding="utf-8")
    assert "rust_ffi_shared {" in android_bp
    assert 'name: "libsecure_core_secretkeeper_binder_bridge"' in android_bp
    assert '"android.hardware.security.secretkeeper-V1-rust"' in android_bp
    assert '"libbinder_rs"' in android_bp
