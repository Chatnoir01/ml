from __future__ import annotations

import ctypes
from pathlib import Path

import pytest

from secure_core_mobile.android_native_bridge import (
    AndroidNativeBridgeCallError,
    AndroidNativeBridgeUnavailable,
    NativeBridgeState,
)
from secure_core_mobile.android_rollback_protected_storage import (
    AndroidRollbackProtectedStorage,
    load_rollback_protected_storage,
)


SOURCE = Path(
    "secure_core_mobile/android_native/rollback_protected_secret_bridge.cpp"
)
ANDROID_BP = Path("secure_core_mobile/android_native/Android.bp")


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
        stored: bytes | None = None,
        write_status: int = 0,
        read_status: int | None = None,
    ) -> None:
        self.stored = stored
        self.write_status = write_status
        self.read_status = read_status
        self.last_written: bytes | None = None
        self.scm_avf_write_rollback_protected_secret = _FakeFunction(
            self._write
        )
        self.scm_avf_read_rollback_protected_secret = _FakeFunction(
            self._read
        )

    def _write(self, data, size):
        if self.write_status != 0:
            return self.write_status
        self.last_written = ctypes.string_at(data, size)
        self.stored = self.last_written
        return 0

    def _read(self, out, size):
        if self.read_status is not None:
            return self.read_status
        if self.stored is None:
            return -24001
        assert len(self.stored) == 32
        for index, value in enumerate(self.stored):
            out[index] = value
        return 0


def test_loader_refuses_non_android_before_loading() -> None:
    called = False

    def loader(path: str):
        nonlocal called
        called = True
        return _Library()

    with pytest.raises(AndroidNativeBridgeUnavailable, match="outside Android"):
        load_rollback_protected_storage(
            "/system/lib64/libsecure_core_avf_attestation_bridge.so",
            platform="linux",
            loader=loader,
        )
    assert called is False


def test_loaded_storage_is_not_platform_proof() -> None:
    storage = load_rollback_protected_storage(
        "/system/lib64/libsecure_core_avf_attestation_bridge.so",
        platform="android",
        loader=lambda path: _Library(),
    )
    assert storage.probe.state is NativeBridgeState.LOADED_UNVERIFIED
    assert storage.probe.trusted_platform_boundary is False


@pytest.mark.parametrize("value", [b"", b"x" * 31, b"x" * 33])
def test_write_requires_exactly_32_bytes(value: bytes) -> None:
    storage = AndroidRollbackProtectedStorage(
        _Library(),
        source_path="/system/lib64/libsecure_core_avf_attestation_bridge.so",
    )
    with pytest.raises(ValueError, match="exactly 32"):
        storage.write(value)


def test_write_and_read_roundtrip_through_native_boundary() -> None:
    library = _Library()
    storage = AndroidRollbackProtectedStorage(
        library,
        source_path="/system/lib64/libsecure_core_avf_attestation_bridge.so",
    )
    value = bytes(range(32))

    storage.write(value)

    assert library.last_written == value
    assert storage.read() == value


def test_not_found_is_distinct_from_access_failure() -> None:
    empty = AndroidRollbackProtectedStorage(
        _Library(),
        source_path="/system/lib64/libsecure_core_avf_attestation_bridge.so",
    )
    assert empty.read() is None

    failed = AndroidRollbackProtectedStorage(
        _Library(read_status=-24003),
        source_path="/system/lib64/libsecure_core_avf_attestation_bridge.so",
    )
    with pytest.raises(AndroidNativeBridgeCallError) as exc:
        failed.read()
    assert exc.value.status == -24003


def test_native_write_error_is_preserved() -> None:
    storage = AndroidRollbackProtectedStorage(
        _Library(write_status=-24003),
        source_path="/system/lib64/libsecure_core_avf_attestation_bridge.so",
    )
    with pytest.raises(AndroidNativeBridgeCallError) as exc:
        storage.write(b"x" * 32)
    assert exc.value.status == -24003


def test_cpp_bridge_uses_vm_payload_api_not_secretkeeper_binder() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "AVmPayload_writeRollbackProtectedSecret" in source
    assert "AVmPayload_readRollbackProtectedSecret" in source

    forbidden = (
        "ISecretkeeper",
        "processSecretManagementRequest",
        "getAuthGraphKe",
        "binder::get_interface",
    )
    for marker in forbidden:
        assert marker not in source


def test_soong_links_rollback_bridge_through_libvm_payload() -> None:
    android_bp = ANDROID_BP.read_text(encoding="utf-8")
    assert '"rollback_protected_secret_bridge.cpp"' in android_bp
    assert 'shared_libs: ["libvm_payload#current"]' in android_bp
