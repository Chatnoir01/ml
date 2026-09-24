"""ctypes adapter for the Android Secretkeeper Binder FFI bridge.

The bridge transports already-protected SecretManagement packets only. Loading
it or completing a Binder call does not establish AuthGraph identity, session
keys, pVM trust, or hostile-host resistance.
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


SCM_SK_BINDER_OK = 0
MAX_PROTECTED_PACKET_BYTES = 1024 * 1024


class _ScmSecretkeeperBinderPacket(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("size", ctypes.c_size_t),
    ]


class AndroidSecretkeeperBinderBridge:
    def __init__(self, library: object, *, source_path: str) -> None:
        required = (
            "scm_secretkeeper_binder_probe_service",
            "scm_secretkeeper_binder_process",
            "scm_secretkeeper_binder_free_packet",
        )
        missing = tuple(name for name in required if not hasattr(library, name))
        if missing:
            raise AndroidNativeBridgeUnavailable(
                "Secretkeeper Binder bridge missing required symbols: "
                + ", ".join(missing)
            )

        self._library = library
        self.source_path = source_path

        probe = library.scm_secretkeeper_binder_probe_service
        probe.argtypes = []
        probe.restype = ctypes.c_int32

        process = library.scm_secretkeeper_binder_process
        process.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(_ScmSecretkeeperBinderPacket),
        ]
        process.restype = ctypes.c_int32

        free_packet = library.scm_secretkeeper_binder_free_packet
        free_packet.argtypes = [
            ctypes.POINTER(_ScmSecretkeeperBinderPacket),
        ]
        free_packet.restype = None

    @property
    def probe(self) -> NativeBridgeProbe:
        return NativeBridgeProbe(
            NativeBridgeState.LOADED_UNVERIFIED,
            self.source_path,
            "secretkeeper-binder-bridge-loaded-authgraph-unverified",
        )

    def probe_service(self) -> bool:
        """Check Binder service reachability without creating an AuthGraph session."""
        status = int(self._library.scm_secretkeeper_binder_probe_service())
        if status == SCM_SK_BINDER_OK:
            return True
        if status == -23002:
            return False
        raise AndroidNativeBridgeCallError(
            "Secretkeeper Binder service probe",
            status,
        )

    def process_protected_packet(self, request: bytes) -> bytes:
        if not isinstance(request, bytes):
            raise TypeError("protected Secretkeeper request must be bytes")
        if not request:
            raise ValueError("protected Secretkeeper request must not be empty")
        if len(request) > MAX_PROTECTED_PACKET_BYTES:
            raise ValueError("protected Secretkeeper request exceeds size limit")

        request_buffer = (
            ctypes.c_uint8 * len(request)
        ).from_buffer_copy(request)
        response = _ScmSecretkeeperBinderPacket()

        status = int(
            self._library.scm_secretkeeper_binder_process(
                request_buffer,
                len(request),
                ctypes.byref(response),
            )
        )
        if status != SCM_SK_BINDER_OK:
            raise AndroidNativeBridgeCallError(
                "Secretkeeper Binder protected-packet transport",
                status,
            )

        try:
            size = int(response.size)
            if size <= 0 or size > MAX_PROTECTED_PACKET_BYTES:
                raise AndroidNativeBridgeUnavailable(
                    "Secretkeeper Binder bridge returned invalid response size"
                )
            if not bool(response.data):
                raise AndroidNativeBridgeUnavailable(
                    "Secretkeeper Binder bridge returned null response"
                )
            return ctypes.string_at(response.data, size)
        finally:
            self._library.scm_secretkeeper_binder_free_packet(
                ctypes.byref(response)
            )


def load_secretkeeper_binder_bridge(
    path: Path | str,
    *,
    platform: str | None = None,
    loader: Callable[[str], object] = ctypes.CDLL,
) -> AndroidSecretkeeperBinderBridge:
    target = sys.platform if platform is None else platform
    if target != "android":
        raise AndroidNativeBridgeUnavailable(
            "Secretkeeper Binder bridge unavailable outside Android runtime"
        )

    candidate = Path(path)
    if not candidate.is_absolute():
        raise ValueError("Secretkeeper Binder bridge path must be absolute")

    try:
        library = loader(str(candidate))
    except (OSError, TypeError) as exc:
        raise AndroidNativeBridgeUnavailable(
            "Secretkeeper Binder bridge could not be loaded"
        ) from exc

    return AndroidSecretkeeperBinderBridge(
        library,
        source_path=str(candidate),
    )
