from __future__ import annotations

from pathlib import Path

import pytest

from secure_core_mobile.aosp_vm_payload_contract import (
    ANDROID_17_R1_VM_PAYLOAD,
    AospVmPayloadSourceTarget,
    VM_PAYLOAD_HEADER,
    VM_PAYLOAD_README,
    VIRTUALIZATION_REPO,
    inspect_vm_payload_contract,
    verify_vm_payload_source_target,
)


def _write(root: Path, relative: Path, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _eligible_tree(root: Path) -> None:
    _write(
        root,
        VM_PAYLOAD_HEADER,
        """
int AVmPayload_requestAttestation(...);
void AVmPayload_getVmInstanceSecret(...);
int AVmPayload_writeRollbackProtectedSecret(...);
int AVmPayload_readRollbackProtectedSecret(...);
bool AVmPayload_isNewInstance(...);
""",
    )
    _write(
        root,
        VM_PAYLOAD_README,
        """
A Microdroid payload cannot connect to any binder server.
Use AVmPayload_runVsockRpcServer to expose Binder RPC from the payload.
""",
    )


def test_eligible_android17_vm_payload_contract_records_digests(
    tmp_path: Path,
) -> None:
    _eligible_tree(tmp_path)

    receipt = inspect_vm_payload_contract(tmp_path)

    assert receipt.eligible_for_secure_core_payload is True
    assert receipt.reason == "required-vm-payload-contract-present"
    assert receipt.has_remote_attestation is True
    assert receipt.has_vm_instance_secret is True
    assert receipt.has_rollback_protected_write is True
    assert receipt.has_rollback_protected_read is True
    assert receipt.has_new_instance_signal is True
    assert receipt.payload_direct_binder_client_forbidden is True
    assert len(receipt.header_sha256) == 64
    assert len(receipt.readme_sha256) == 64
    assert len(receipt.receipt_sha256) == 64


@pytest.mark.parametrize(
    ("missing_marker", "reason_marker"),
    [
        ("AVmPayload_writeRollbackProtectedSecret", "rollback-protected-write"),
        ("AVmPayload_readRollbackProtectedSecret", "rollback-protected-read"),
        ("AVmPayload_isNewInstance", "new-instance-signal"),
    ],
)
def test_missing_required_vm_payload_api_is_rejected(
    tmp_path: Path,
    missing_marker: str,
    reason_marker: str,
) -> None:
    _eligible_tree(tmp_path)
    header_path = tmp_path / VM_PAYLOAD_HEADER
    header_path.write_text(
        header_path.read_text(encoding="utf-8").replace(missing_marker, "REMOVED"),
        encoding="utf-8",
    )

    receipt = inspect_vm_payload_contract(tmp_path)

    assert receipt.eligible_for_secure_core_payload is False
    assert reason_marker in receipt.reason


def test_payload_contract_rejects_missing_binder_client_restriction(
    tmp_path: Path,
) -> None:
    _eligible_tree(tmp_path)
    _write(
        tmp_path,
        VM_PAYLOAD_README,
        "Use AVmPayload_runVsockRpcServer for RPC.",
    )

    receipt = inspect_vm_payload_contract(tmp_path)

    assert receipt.payload_direct_binder_client_forbidden is False
    assert receipt.eligible_for_secure_core_payload is False
    assert "payload-binder-client-restriction" in receipt.reason


def test_android17_virtualization_target_pins_exact_commit(
    tmp_path: Path,
) -> None:
    expected_repo = tmp_path / VIRTUALIZATION_REPO

    verify_vm_payload_source_target(
        tmp_path,
        ANDROID_17_R1_VM_PAYLOAD,
        git_head_reader=lambda path: (
            ANDROID_17_R1_VM_PAYLOAD.virtualization_commit
            if path == expected_repo
            else "0" * 40
        ),
    )

    assert ANDROID_17_R1_VM_PAYLOAD.name == "android-17.0.0_r1"
    assert (
        ANDROID_17_R1_VM_PAYLOAD.virtualization_commit
        == "22f1c9ee92b146e10c8f5e71338618f77ab1631e"
    )


def test_virtualization_revision_mismatch_is_rejected(tmp_path: Path) -> None:
    target = AospVmPayloadSourceTarget(
        name="test",
        virtualization_commit="1" * 40,
    )

    with pytest.raises(ValueError, match="Virtualization revision mismatch"):
        verify_vm_payload_source_target(
            tmp_path,
            target,
            git_head_reader=lambda path: "2" * 40,
        )


def test_vm_payload_source_symlink_is_rejected(tmp_path: Path) -> None:
    _eligible_tree(tmp_path)
    source = tmp_path / VM_PAYLOAD_HEADER
    real = tmp_path / "real-vm-payload.h"
    real.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    source.unlink()
    source.symlink_to(real)

    with pytest.raises(ValueError, match="symlink"):
        inspect_vm_payload_contract(tmp_path)
