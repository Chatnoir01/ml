"""Offline contract gate for the Microdroid VM Payload API used by Secure Core.

The payload path must use libvm_payload rather than direct Binder client access.
This inspector pins the exact source revision and verifies that the Android 17
rollback-protected storage and attestation functions are present.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Callable


VM_PAYLOAD_CONTRACT_SCHEMA_VERSION = 1
MAX_SOURCE_BYTES = 4 * 1024 * 1024

VIRTUALIZATION_REPO = Path("packages/modules/Virtualization")
VM_PAYLOAD_HEADER = VIRTUALIZATION_REPO / Path(
    "libs/libvm_payload/include/vm_payload.h"
)
VM_PAYLOAD_README = VIRTUALIZATION_REPO / Path(
    "libs/libvm_payload/README.md"
)


@dataclass(frozen=True)
class AospVmPayloadSourceTarget:
    name: str
    virtualization_commit: str


ANDROID_17_R1_VM_PAYLOAD = AospVmPayloadSourceTarget(
    name="android-17.0.0_r1",
    virtualization_commit="22f1c9ee92b146e10c8f5e71338618f77ab1631e",
)

KNOWN_VM_PAYLOAD_TARGETS = {
    ANDROID_17_R1_VM_PAYLOAD.name: ANDROID_17_R1_VM_PAYLOAD,
}


@dataclass(frozen=True)
class VmPayloadContractReceipt:
    schema_version: int
    header_sha256: str
    readme_sha256: str
    has_remote_attestation: bool
    has_vm_instance_secret: bool
    has_rollback_protected_write: bool
    has_rollback_protected_read: bool
    has_new_instance_signal: bool
    payload_direct_binder_client_forbidden: bool
    eligible_for_secure_core_payload: bool
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
        raise ValueError(f"VM Payload contract source symlink rejected: {relative}")
    if not path.is_file():
        raise ValueError(f"VM Payload contract source missing: {relative}")
    size = path.stat().st_size
    if size <= 0 or size > MAX_SOURCE_BYTES:
        raise ValueError(f"VM Payload contract source size invalid: {relative}")
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"VM Payload contract source is not UTF-8: {relative}") from exc
    return text, hashlib.sha256(data).hexdigest()


def _git_head(repository: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("unable to inspect Virtualization repository") from exc
    if result.returncode != 0:
        raise ValueError("unable to resolve Virtualization repository HEAD")
    head = result.stdout.strip().lower()
    try:
        if len(head) != 40 or len(bytes.fromhex(head)) != 20:
            raise ValueError
    except ValueError as exc:
        raise ValueError("invalid Virtualization repository HEAD") from exc
    return head


def verify_vm_payload_source_target(
    aosp_root: Path | str,
    target: AospVmPayloadSourceTarget,
    *,
    git_head_reader: Callable[[Path], str] = _git_head,
) -> None:
    if not isinstance(target, AospVmPayloadSourceTarget):
        raise TypeError("VM Payload source target required")
    repository = Path(aosp_root) / VIRTUALIZATION_REPO
    actual = git_head_reader(repository).strip().lower()
    expected = target.virtualization_commit.lower()
    if actual != expected:
        raise ValueError(
            f"AOSP Virtualization revision mismatch: expected {expected}, got {actual}"
        )


def inspect_vm_payload_contract(
    aosp_root: Path | str,
) -> VmPayloadContractReceipt:
    root = Path(aosp_root)
    if root.is_symlink():
        raise ValueError("AOSP root symlink rejected")
    if not root.is_dir():
        raise ValueError("AOSP root unavailable")

    header, header_sha = _read_source(root, VM_PAYLOAD_HEADER)
    readme, readme_sha = _read_source(root, VM_PAYLOAD_README)

    attestation = "AVmPayload_requestAttestation" in header
    vm_secret = "AVmPayload_getVmInstanceSecret" in header
    rollback_write = "AVmPayload_writeRollbackProtectedSecret" in header
    rollback_read = "AVmPayload_readRollbackProtectedSecret" in header
    new_instance = "AVmPayload_isNewInstance" in header
    binder_forbidden = (
        "cannot connect to any binder server" in readme
        and "AVmPayload_runVsockRpcServer" in readme
    )

    eligible = all((
        attestation,
        vm_secret,
        rollback_write,
        rollback_read,
        new_instance,
        binder_forbidden,
    ))

    if eligible:
        reason = "required-vm-payload-contract-present"
    else:
        missing = []
        if not attestation:
            missing.append("remote-attestation")
        if not vm_secret:
            missing.append("vm-instance-secret")
        if not rollback_write:
            missing.append("rollback-protected-write")
        if not rollback_read:
            missing.append("rollback-protected-read")
        if not new_instance:
            missing.append("new-instance-signal")
        if not binder_forbidden:
            missing.append("payload-binder-client-restriction")
        reason = "missing:" + ",".join(missing)

    return VmPayloadContractReceipt(
        schema_version=VM_PAYLOAD_CONTRACT_SCHEMA_VERSION,
        header_sha256=header_sha,
        readme_sha256=readme_sha,
        has_remote_attestation=attestation,
        has_vm_instance_secret=vm_secret,
        has_rollback_protected_write=rollback_write,
        has_rollback_protected_read=rollback_read,
        has_new_instance_signal=new_instance,
        payload_direct_binder_client_forbidden=binder_forbidden,
        eligible_for_secure_core_payload=eligible,
        reason=reason,
    )
