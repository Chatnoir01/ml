"""ctypes adapter for Microdroid VM Payload rollback-protected storage.

The underlying Android 17 API is backed by Microdroid Manager/Secretkeeper on
supported devices. Successful I/O is platform functionality, not by itself
proof that this process is inside an independently verified pVM boundary.
"""

from __future__ import annotations

import ctypes
from pathlib import Path
import sys
from typing import Callable

from .android_native_bridge import (
    AndroidNativeBridgeCallError,
    AndroidNativeBridgeUnavailable,
    NativeBridgeProbe,
    NativeBridgeState,
)


SCM_RP_OK = 0
SCM_RP_NOT_FOUND = -24001
SCM_RP_SECRET_BYTES = 32


class AndroidRollbackProtectedStorage:
    def __init__(self, library: object, *, source_path: str) -> None:
        required = (
            "scm_avf_write_rollback_protected_secret",
            "scm_avf_read_rollback_protected_secret",
        )
        missing = tuple(name for name in required if not hasattr(library, name))
        if missing:
            raise AndroidNativeBridgeUnavailable(
                "rollback-protected storage bridge missing required symbols: "
                + ", ".join(missing)
            )

        self._library = library
        self.source_path = source_path

        write = library.scm_avf_write_rollback_protected_secret
        write.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
        write.restype = ctypes.c_int32

        read = library.scm_avf_read_rollback_protected_secret
        read.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
        read.restype = ctypes.c_int32

    @property
    def probe(self) -> NativeBridgeProbe:
        return NativeBridgeProbe(
            NativeBridgeState.LOADED_UNVERIFIED,
            self.source_path,
            "rollback-protected-vm-payload-api-loaded-boundary-unverified",
        )

    def write(self, value: bytes) -> None:
        if not isinstance(value, bytes):
            raise TypeError("rollback-protected value must be bytes")
        if len(value) != SCM_RP_SECRET_BYTES:
            raise ValueError("rollback-protected value must be exactly 32 bytes")

        buffer = (
            ctypes.c_uint8 * SCM_RP_SECRET_BYTES
        ).from_buffer_copy(value)
        status = int(
            self._library.scm_avf_write_rollback_protected_secret(
                buffer,
                SCM_RP_SECRET_BYTES,
            )
        )
        if status != SCM_RP_OK:
            raise AndroidNativeBridgeCallError(
                "VM Payload rollback-protected write",
                status,
            )

    def read(self) -> bytes | None:
        out = (ctypes.c_uint8 * SCM_RP_SECRET_BYTES)()
        status = int(
            self._library.scm_avf_read_rollback_protected_secret(
                out,
                SCM_RP_SECRET_BYTES,
            )
        )
        if status == SCM_RP_NOT_FOUND:
            return None
        if status != SCM_RP_OK:
            raise AndroidNativeBridgeCallError(
                "VM Payload rollback-protected read",
                status,
            )
        return bytes(out)


def load_rollback_protected_storage(
    path: Path | str,
    *,
    platform: str | None = None,
    loader: Callable[[str], object] = ctypes.CDLL,
) -> AndroidRollbackProtectedStorage:
    target = sys.platform if platform is None else platform
    if target != "android":
        raise AndroidNativeBridgeUnavailable(
            "rollback-protected VM Payload storage unavailable outside Android runtime"
        )

    candidate = Path(path)
    if not candidate.is_absolute():
        raise ValueError("rollback-protected bridge path must be absolute")

    try:
        library = loader(str(candidate))
    except (OSError, TypeError) as exc:
        raise AndroidNativeBridgeUnavailable(
            "rollback-protected VM Payload bridge could not be loaded"
        ) from exc

    return AndroidRollbackProtectedStorage(
        library,
        source_path=str(candidate),
    )
