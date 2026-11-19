"""Secret-free preflight for the compiled Android native bridge.

This diagnostic can prove that the bridge ABI is loadable and that native calls
return data. It cannot prove that the process is executing inside the intended
pVM and therefore never emits platform trust capability tokens.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Callable

from .android_native_bridge import (
    AndroidNativeBridgeCallError,
    AndroidNativeBridgeUnavailable,
    load_android_native_bridge,
)
from .compat import StrEnum


NATIVE_PREFLIGHT_SCHEMA_VERSION = 1
SCM_AVF_PROFILE_PIN_NOT_PROVISIONED = -21002


class AndroidNativePreflightState(StrEnum):
    NON_ANDROID_RUNTIME = "NON_ANDROID_RUNTIME"
    BRIDGE_UNAVAILABLE = "BRIDGE_UNAVAILABLE"
    BRIDGE_LOADED_UNVERIFIED = "BRIDGE_LOADED_UNVERIFIED"
    PROFILE_PIN_PRESENT_UNVERIFIED = "PROFILE_PIN_PRESENT_UNVERIFIED"
    ATTESTATION_OBSERVED_UNVERIFIED = "ATTESTATION_OBSERVED_UNVERIFIED"


@dataclass(frozen=True)
class AndroidNativePreflightReceipt:
    schema_version: int
    state: AndroidNativePreflightState
    bridge_path: str
    bridge_loaded: bool
    profile_pin_present: bool
    profile_pin_sha256: str | None
    profile_pin_native_status: int | None
    attestation_requested: bool
    attestation_observed: bool
    challenge_sha256: str | None
    certificate_count: int
    certificate_chain_sha256: str | None
    attestation_native_status: int | None
    trusted_platform_boundary: bool
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


def _chain_digest(certificates: tuple[bytes, ...]) -> str:
    digest = hashlib.sha256()
    digest.update(b"SCM-AVF-NATIVE-CHAIN-V1\x00")
    for certificate in certificates:
        digest.update(len(certificate).to_bytes(8, "big"))
        digest.update(certificate)
    return digest.hexdigest()


def run_android_native_preflight(
    *,
    bridge_path: Path | str,
    challenge: bytes | None = None,
    platform: str | None = None,
    loader: Callable[[str], object] | None = None,
) -> AndroidNativePreflightReceipt:
    path_text = str(Path(bridge_path))

    load_kwargs = {
        "platform": platform,
    }
    if loader is not None:
        load_kwargs["loader"] = loader

    try:
        bridge = load_android_native_bridge(bridge_path, **load_kwargs)
    except AndroidNativeBridgeUnavailable as exc:
        non_android = "outside Android runtime" in str(exc)
        return AndroidNativePreflightReceipt(
            schema_version=NATIVE_PREFLIGHT_SCHEMA_VERSION,
            state=(
                AndroidNativePreflightState.NON_ANDROID_RUNTIME
                if non_android
                else AndroidNativePreflightState.BRIDGE_UNAVAILABLE
            ),
            bridge_path=path_text,
            bridge_loaded=False,
            profile_pin_present=False,
            profile_pin_sha256=None,
            profile_pin_native_status=None,
            attestation_requested=challenge is not None,
            attestation_observed=False,
            challenge_sha256=(
                hashlib.sha256(challenge).hexdigest()
                if challenge is not None
                else None
            ),
            certificate_count=0,
            certificate_chain_sha256=None,
            attestation_native_status=None,
            trusted_platform_boundary=False,
            reason=(
                "android-runtime-not-detected"
                if non_android
                else "native-bridge-unavailable"
            ),
        )
    except ValueError:
        raise

    pin_present = False
    pin_sha = None
    pin_status = None
    try:
        raw_pin = bridge.load_preprovisioned_profile_pin_bytes()
        pin_present = True
        pin_sha = hashlib.sha256(raw_pin).hexdigest()
    except AndroidNativeBridgeCallError as exc:
        pin_status = exc.status
        if exc.status != SCM_AVF_PROFILE_PIN_NOT_PROVISIONED:
            # Diagnostic status is retained, but no trust is inferred.
            pin_present = False

    attestation_requested = challenge is not None
    attestation_observed = False
    attestation_status = None
    certificate_count = 0
    chain_sha = None
    challenge_sha = None

    if challenge is not None:
        challenge_sha = hashlib.sha256(challenge).hexdigest()
        try:
            certificates = bridge.request_avf_attestation(challenge)
            certificate_count = len(certificates)
            chain_sha = _chain_digest(certificates)
            attestation_observed = True
        except AndroidNativeBridgeCallError as exc:
            attestation_status = exc.status
        except AndroidNativeBridgeUnavailable:
            attestation_status = None

    if attestation_observed:
        state = AndroidNativePreflightState.ATTESTATION_OBSERVED_UNVERIFIED
        reason = "native-attestation-observed-platform-verification-required"
    elif pin_present:
        state = AndroidNativePreflightState.PROFILE_PIN_PRESENT_UNVERIFIED
        reason = "native-profile-pin-present-platform-verification-required"
    else:
        state = AndroidNativePreflightState.BRIDGE_LOADED_UNVERIFIED
        reason = "native-bridge-loaded-platform-boundary-unverified"

    return AndroidNativePreflightReceipt(
        schema_version=NATIVE_PREFLIGHT_SCHEMA_VERSION,
        state=state,
        bridge_path=path_text,
        bridge_loaded=True,
        profile_pin_present=pin_present,
        profile_pin_sha256=pin_sha,
        profile_pin_native_status=pin_status,
        attestation_requested=attestation_requested,
        attestation_observed=attestation_observed,
        challenge_sha256=challenge_sha,
        certificate_count=certificate_count,
        certificate_chain_sha256=chain_sha,
        attestation_native_status=attestation_status,
        trusted_platform_boundary=False,
        reason=reason,
    )
