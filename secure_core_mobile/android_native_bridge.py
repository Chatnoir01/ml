"""ctypes boundary for the Secure Core Android native bridge.

Loading a shared library or successfully calling its C ABI is transport
availability only. It does not prove that the process is executing inside the
intended pVM and therefore cannot itself create PLATFORM_VERIFIED evidence.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Callable

from .compat import StrEnum


SCM_AVF_BRIDGE_OK = 0
SCM_AVF_PROFILE_PIN_OK = 0
SCM_AVF_PROFILE_PIN_BYTES = 32
MAX_CHALLENGE_BYTES = 64
MAX_CERTIFICATES = 16
MAX_CERTIFICATE_BYTES = 64 * 1024
MAX_CERTIFICATE_CHAIN_BYTES = 512 * 1024


class NativeBridgeState(StrEnum):
    UNAVAILABLE = "UNAVAILABLE"
    LOADED_UNVERIFIED = "LOADED_UNVERIFIED"


@dataclass(frozen=True)
class NativeBridgeProbe:
    state: NativeBridgeState
    source_path: str | None
    reason: str

    @property
    def trusted_platform_boundary(self) -> bool:
        return False


class AndroidNativeBridgeUnavailable(RuntimeError):
    pass


class AndroidNativeBridgeCallError(RuntimeError):
    def __init__(self, operation: str, status: int) -> None:
        super().__init__(f"{operation} failed with native status {status}")
        self.operation = operation
        self.status = int(status)


class _ScmAvfCertificate(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("size", ctypes.c_size_t),
    ]


class _ScmAvfCertificateChain(ctypes.Structure):
    _fields_ = [
        ("certificates", ctypes.POINTER(_ScmAvfCertificate)),
        ("certificate_count", ctypes.c_size_t),
    ]


_REQUIRED_SYMBOLS = (
    "scm_avf_request_attestation",
    "scm_avf_free_certificate_chain",
    "scm_avf_load_preprovisioned_profile_pin",
    "scm_secretkeeper_process_protected_packet",
    "scm_secretkeeper_free_packet",
)


def _runtime_is_android(platform: str | None) -> bool:
    return (sys.platform if platform is None else platform) == "android"


class AndroidNativeBridge:
    """Loaded native ABI handle.

    The object intentionally exposes no method that emits platform trust
    capability tokens. Its outputs are raw native transport data only.
    """

    def __init__(self, library: object, *, source_path: str) -> None:
        missing = tuple(name for name in _REQUIRED_SYMBOLS if not hasattr(library, name))
        if missing:
            raise AndroidNativeBridgeUnavailable(
                "native bridge missing required symbols: " + ", ".join(missing)
            )
        self._library = library
        self.source_path = source_path

        self._configure_signatures()

    def _configure_signatures(self) -> None:
        request = self._library.scm_avf_request_attestation
        request.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(_ScmAvfCertificateChain),
        ]
        request.restype = ctypes.c_int32

        free_chain = self._library.scm_avf_free_certificate_chain
        free_chain.argtypes = [ctypes.POINTER(_ScmAvfCertificateChain)]
        free_chain.restype = None

        load_pin = self._library.scm_avf_load_preprovisioned_profile_pin
        load_pin.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
        ]
        load_pin.restype = ctypes.c_int32

    @property
    def probe(self) -> NativeBridgeProbe:
        return NativeBridgeProbe(
            NativeBridgeState.LOADED_UNVERIFIED,
            self.source_path,
            "native-bridge-loaded-platform-boundary-unverified",
        )

    def request_avf_attestation(self, challenge: bytes) -> tuple[bytes, ...]:
        if not isinstance(challenge, bytes):
            raise TypeError("AVF challenge must be bytes")
        if not challenge or len(challenge) > MAX_CHALLENGE_BYTES:
            raise ValueError("AVF challenge must contain 1..64 bytes")

        challenge_buffer = (ctypes.c_uint8 * len(challenge)).from_buffer_copy(challenge)
        chain = _ScmAvfCertificateChain()

        status = int(
            self._library.scm_avf_request_attestation(
                challenge_buffer,
                len(challenge),
                ctypes.byref(chain),
            )
        )
        if status != SCM_AVF_BRIDGE_OK:
            raise AndroidNativeBridgeCallError("AVF attestation", status)

        try:
            count = int(chain.certificate_count)
            if count <= 0 or count > MAX_CERTIFICATES:
                raise AndroidNativeBridgeUnavailable(
                    "native AVF bridge returned invalid certificate count"
                )
            if not bool(chain.certificates):
                raise AndroidNativeBridgeUnavailable(
                    "native AVF bridge returned null certificate array"
                )

            total = 0
            certificates: list[bytes] = []
            for index in range(count):
                cert = chain.certificates[index]
                size = int(cert.size)
                if size <= 0 or size > MAX_CERTIFICATE_BYTES:
                    raise AndroidNativeBridgeUnavailable(
                        "native AVF bridge returned invalid certificate size"
                    )
                if total > MAX_CERTIFICATE_CHAIN_BYTES - size:
                    raise AndroidNativeBridgeUnavailable(
                        "native AVF bridge returned oversized certificate chain"
                    )
                if not bool(cert.data):
                    raise AndroidNativeBridgeUnavailable(
                        "native AVF bridge returned null certificate data"
                    )
                certificates.append(ctypes.string_at(cert.data, size))
                total += size

            return tuple(certificates)
        finally:
            self._library.scm_avf_free_certificate_chain(ctypes.byref(chain))

    def load_preprovisioned_profile_pin_bytes(self) -> bytes:
        """Read native pin bytes without promoting them to protected evidence."""
        out = (ctypes.c_uint8 * SCM_AVF_PROFILE_PIN_BYTES)()
        status = int(
            self._library.scm_avf_load_preprovisioned_profile_pin(
                out,
                SCM_AVF_PROFILE_PIN_BYTES,
            )
        )
        if status != SCM_AVF_PROFILE_PIN_OK:
            raise AndroidNativeBridgeCallError("AVF profile pin load", status)
        return bytes(out)


def load_android_native_bridge(
    path: Path | str,
    *,
    platform: str | None = None,
    loader: Callable[[str], object] = ctypes.CDLL,
) -> AndroidNativeBridge:
    if not _runtime_is_android(platform):
        raise AndroidNativeBridgeUnavailable(
            "Android native bridge unavailable outside Android runtime"
        )

    candidate = Path(path)
    if not candidate.is_absolute():
        raise ValueError("native bridge path must be absolute")

    try:
        library = loader(str(candidate))
    except (OSError, TypeError) as exc:
        raise AndroidNativeBridgeUnavailable(
            "Android native bridge could not be loaded"
        ) from exc

    return AndroidNativeBridge(library, source_path=str(candidate))
