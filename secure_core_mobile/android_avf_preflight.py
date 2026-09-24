"""Executable Android/AVF guest preflight.

The preflight answers only whether observable prerequisites are present. It does
not promote AVF presence, a readable Secretkeeper key, or synthetic platform
evidence into hostile-host readiness.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Callable

from .compat import StrEnum
from .platform_evidence import PlatformVerification
from .secretkeeper_cose_key import parse_secretkeeper_cose_key
from .secretkeeper_dt import (
    TRUSTED_SECRETKEEPER_DT_PATH,
    read_pvmfw_secretkeeper_key,
)
from .avf_platform_verifier import (
    PreprovisionedAvfProfilePin,
    ProtectedAvfProfilePinProviderUnavailable,
)


PREFLIGHT_SCHEMA_VERSION = 1


class AvfGuestPreflightState(StrEnum):
    NON_ANDROID_RUNTIME = "NON_ANDROID_RUNTIME"
    SECRETKEEPER_DT_UNAVAILABLE = "SECRETKEEPER_DT_UNAVAILABLE"
    SECRETKEEPER_KEY_VALID = "SECRETKEEPER_KEY_VALID"
    PLATFORM_EVIDENCE_BOUND = "PLATFORM_EVIDENCE_BOUND"


@dataclass(frozen=True)
class AvfGuestPreflightReceipt:
    schema_version: int
    state: AvfGuestPreflightState
    android_runtime_detected: bool
    secretkeeper_dt_path: str
    secretkeeper_key_profile: str | None
    secretkeeper_key_sha256: str | None
    platform_verified: bool
    protected_profile_pin_loaded: bool
    native_authgraph_available: bool
    hostile_host_ready: bool
    reason: str

    def canonical_bytes(self) -> bytes:
        payload = asdict(self)
        payload["state"] = str(self.state)
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

    @property
    def receipt_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def detect_android_runtime(
    *,
    platform: str | None = None,
    exists: Callable[[Path], bool] | None = None,
) -> bool:
    target = sys.platform if platform is None else platform
    if target == "android":
        return True

    checker = Path.exists if exists is None else exists
    markers = (
        Path("/system/build.prop"),
        Path("/system/bin/getprop"),
        Path("/apex"),
    )
    return any(bool(checker(marker)) for marker in markers)


def run_avf_guest_preflight(
    *,
    platform: str | None = None,
    exists: Callable[[Path], bool] | None = None,
    secretkeeper_reader: Callable[[Path], bytes] | None = None,
    platform_verification: PlatformVerification | None = None,
    protected_pin_provider: object | None = None,
    native_authgraph_available: bool = False,
) -> AvfGuestPreflightReceipt:
    android = detect_android_runtime(platform=platform, exists=exists)
    if not android:
        return AvfGuestPreflightReceipt(
            schema_version=PREFLIGHT_SCHEMA_VERSION,
            state=AvfGuestPreflightState.NON_ANDROID_RUNTIME,
            android_runtime_detected=False,
            secretkeeper_dt_path=str(TRUSTED_SECRETKEEPER_DT_PATH),
            secretkeeper_key_profile=None,
            secretkeeper_key_sha256=None,
            platform_verified=False,
            protected_profile_pin_loaded=False,
            native_authgraph_available=False,
            hostile_host_ready=False,
            reason="android-runtime-not-detected",
        )

    try:
        if secretkeeper_reader is None:
            key = read_pvmfw_secretkeeper_key()
        else:
            key = read_pvmfw_secretkeeper_key(reader=secretkeeper_reader)
        parsed = parse_secretkeeper_cose_key(key.public_key_cbor)
    except (OSError, RuntimeError, TypeError, ValueError):
        return AvfGuestPreflightReceipt(
            schema_version=PREFLIGHT_SCHEMA_VERSION,
            state=AvfGuestPreflightState.SECRETKEEPER_DT_UNAVAILABLE,
            android_runtime_detected=True,
            secretkeeper_dt_path=str(TRUSTED_SECRETKEEPER_DT_PATH),
            secretkeeper_key_profile=None,
            secretkeeper_key_sha256=None,
            platform_verified=False,
            protected_profile_pin_loaded=False,
            native_authgraph_available=bool(native_authgraph_available),
            hostile_host_ready=False,
            reason="secretkeeper-dt-key-unavailable-or-invalid",
        )

    platform_verified = (
        isinstance(platform_verification, PlatformVerification)
        and platform_verification.qualifies_as_android_avf
    )

    provider = (
        ProtectedAvfProfilePinProviderUnavailable()
        if protected_pin_provider is None
        else protected_pin_provider
    )
    protected_pin_loaded = False
    try:
        pin = provider.load()
        protected_pin_loaded = isinstance(pin, PreprovisionedAvfProfilePin)
    except (AttributeError, RuntimeError, TypeError, ValueError):
        protected_pin_loaded = False

    # Native AuthGraph/Binder transport is still a separate mandatory gate.
    hostile_ready = (
        platform_verified
        and protected_pin_loaded
        and bool(native_authgraph_available)
    )

    state = (
        AvfGuestPreflightState.PLATFORM_EVIDENCE_BOUND
        if platform_verified
        else AvfGuestPreflightState.SECRETKEEPER_KEY_VALID
    )
    if hostile_ready:
        reason = "all-modeled-preflight-gates-present"
    elif not platform_verified:
        reason = "secretkeeper-key-valid-platform-evidence-not-authoritative"
    elif not protected_pin_loaded:
        reason = "platform-verified-protected-profile-pin-unavailable"
    else:
        reason = "platform-verified-native-authgraph-unavailable"

    return AvfGuestPreflightReceipt(
        schema_version=PREFLIGHT_SCHEMA_VERSION,
        state=state,
        android_runtime_detected=True,
        secretkeeper_dt_path=str(TRUSTED_SECRETKEEPER_DT_PATH),
        secretkeeper_key_profile=parsed.profile,
        secretkeeper_key_sha256=parsed.encoded_sha256,
        platform_verified=platform_verified,
        protected_profile_pin_loaded=protected_pin_loaded,
        native_authgraph_available=bool(native_authgraph_available),
        hostile_host_ready=hostile_ready,
        reason=reason,
    )
