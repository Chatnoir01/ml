"""Offline AOSP Secretkeeper/AuthGraph source-contract preflight.

The native AuthGraph layer must not guess which AOSP SkSession API is present.
This inspector records the exact local source snapshot and requires the
identity-binding features Secure Core needs before a native session bridge may
be considered eligible for implementation/build.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path


AOSP_CONTRACT_SCHEMA_VERSION = 1
MAX_SOURCE_BYTES = 4 * 1024 * 1024

ISECRETKEEPER_AIDL = Path(
    "hardware/interfaces/security/secretkeeper/aidl/aidl_api/"
    "android.hardware.security.secretkeeper/current/"
    "android/hardware/security/secretkeeper/ISecretkeeper.aidl"
)
SECRETKEEPER_CLIENT = Path("system/secretkeeper/client/src/lib.rs")
SECRETKEEPER_VTS_CLIENT = Path(
    "hardware/interfaces/security/secretkeeper/aidl/vts/"
    "secretkeeper_test_client.rs"
)


@dataclass(frozen=True)
class AospSecretkeeperContractReceipt:
    schema_version: int
    aidl_sha256: str
    client_sha256: str
    vts_client_sha256: str
    has_process_secret_management_request: bool
    has_get_authgraph_ke: bool
    has_sk_session: bool
    has_explicit_dice_identity: bool
    has_expected_secretkeeper_identity_binding: bool
    vts_exercises_expected_identity_binding: bool
    eligible_for_secure_core_native_authgraph: bool
    reason: str

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            asdict(self),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

    @property
    def receipt_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _read_source(root: Path, relative: Path) -> tuple[str, str]:
    path = root / relative
    if path.is_symlink():
        raise ValueError(f"AOSP contract source symlink rejected: {relative}")
    if not path.is_file():
        raise ValueError(f"AOSP contract source missing: {relative}")

    size = path.stat().st_size
    if size <= 0 or size > MAX_SOURCE_BYTES:
        raise ValueError(f"AOSP contract source size invalid: {relative}")

    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"AOSP contract source is not UTF-8: {relative}"
        ) from exc
    return text, hashlib.sha256(data).hexdigest()


def inspect_aosp_secretkeeper_contract(
    aosp_root: Path | str,
) -> AospSecretkeeperContractReceipt:
    root = Path(aosp_root)
    if root.is_symlink():
        raise ValueError("AOSP root symlink rejected")
    if not root.is_dir():
        raise ValueError("AOSP root unavailable")

    aidl, aidl_sha = _read_source(root, ISECRETKEEPER_AIDL)
    client, client_sha = _read_source(root, SECRETKEEPER_CLIENT)
    vts, vts_sha = _read_source(root, SECRETKEEPER_VTS_CLIENT)

    process = "processSecretManagementRequest" in aidl
    authgraph = "getAuthGraphKe" in aidl
    sk_session = "pub struct SkSession" in client
    explicit_dice = "OwnedDiceArtifactsWithExplicitKey" in client
    expected_identity = (
        "expected_sk_key" in client
        and "CoseKey" in client
    )
    vts_expected_identity = (
        "with_expected_sk_identity" in vts
        or (
            "expected_sk_key" in vts
            and "SkSession::new" in vts
        )
    )

    eligible = all((
        process,
        authgraph,
        sk_session,
        explicit_dice,
        expected_identity,
        vts_expected_identity,
    ))

    if eligible:
        reason = "required-secretkeeper-authgraph-contract-present"
    else:
        missing = []
        if not process:
            missing.append("processSecretManagementRequest")
        if not authgraph:
            missing.append("getAuthGraphKe")
        if not sk_session:
            missing.append("SkSession")
        if not explicit_dice:
            missing.append("explicit-DICE-identity")
        if not expected_identity:
            missing.append("expected-Secretkeeper-identity-binding")
        if not vts_expected_identity:
            missing.append("VTS-expected-identity-coverage")
        reason = "missing:" + ",".join(missing)

    return AospSecretkeeperContractReceipt(
        schema_version=AOSP_CONTRACT_SCHEMA_VERSION,
        aidl_sha256=aidl_sha,
        client_sha256=client_sha,
        vts_client_sha256=vts_sha,
        has_process_secret_management_request=process,
        has_get_authgraph_ke=authgraph,
        has_sk_session=sk_session,
        has_explicit_dice_identity=explicit_dice,
        has_expected_secretkeeper_identity_binding=expected_identity,
        vts_exercises_expected_identity_binding=vts_expected_identity,
        eligible_for_secure_core_native_authgraph=eligible,
        reason=reason,
    )
