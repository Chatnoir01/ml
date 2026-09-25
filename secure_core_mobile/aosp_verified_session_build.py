"""Executable Soong build gate for the verified Secretkeeper session wrapper.

This gate is intentionally stricter than invoking Soong directly. It first
requires the reviewed Android 17 Secretkeeper source revisions and an exact
AOSP Secretkeeper contract lock, then verifies the Secure Core Rust module is
present inside the same AOSP tree before building it.

A successful receipt proves only that the source-level integration compiled in
that checkout. It is not hardware, pVM, or hostile-host evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Callable

from .aosp_secretkeeper_contract import (
    ANDROID_SECURITY_17_R1,
    inspect_aosp_secretkeeper_contract,
    load_aosp_secretkeeper_contract_lock,
    verify_aosp_secretkeeper_contract_lock,
    verify_aosp_secretkeeper_source_target,
)


AOSP_VERIFIED_SESSION_BUILD_SCHEMA_VERSION = 1
VERIFIED_SESSION_MODULE = "libsecure_core_secretkeeper_verified_session"
SOONG_UI = Path("build/soong/soong_ui.bash")
ANDROID_BP = Path("Android.bp")
VERIFIED_SESSION_RUST = Path("secretkeeper_verified_session.rs")
MAX_BUILD_SOURCE_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class AospVerifiedSessionBuildReceipt:
    schema_version: int
    source_target: str
    module_name: str
    secretkeeper_contract_receipt_sha256: str
    contract_lock_sha256: str
    android_bp_sha256: str
    rust_source_sha256: str
    command_sha256: str
    stdout_sha256: str
    stderr_sha256: str
    returncode: int
    build_succeeded: bool
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


def _read_build_source(path: Path, *, label: str) -> tuple[str, str]:
    if path.is_symlink():
        raise ValueError(f"{label} symlink rejected")
    if not path.is_file():
        raise ValueError(f"{label} unavailable")
    size = path.stat().st_size
    if size <= 0 or size > MAX_BUILD_SOURCE_BYTES:
        raise ValueError(f"{label} size invalid")
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} is not UTF-8") from exc
    return text, hashlib.sha256(data).hexdigest()


def _default_runner(
    command: list[str],
    *,
    cwd: Path,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def run_verified_session_soong_build(
    *,
    aosp_root: Path | str,
    secure_core_android_native_dir: Path | str,
    contract_lock_path: Path | str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = _default_runner,
    timeout: int = 1800,
    git_head_reader: Callable[[Path], str] | None = None,
) -> AospVerifiedSessionBuildReceipt:
    root = Path(aosp_root)
    if root.is_symlink():
        raise ValueError("AOSP root symlink rejected")
    if not root.is_dir():
        raise ValueError("AOSP root unavailable")
    if timeout <= 0:
        raise ValueError("Soong build timeout must be positive")

    if git_head_reader is None:
        verify_aosp_secretkeeper_source_target(root, ANDROID_SECURITY_17_R1)
    else:
        verify_aosp_secretkeeper_source_target(
            root,
            ANDROID_SECURITY_17_R1,
            git_head_reader=git_head_reader,
        )
    contract = inspect_aosp_secretkeeper_contract(root)
    lock = load_aosp_secretkeeper_contract_lock(contract_lock_path)
    verify_aosp_secretkeeper_contract_lock(contract, lock)

    native_dir = Path(secure_core_android_native_dir)
    if native_dir.is_symlink():
        raise ValueError("Secure Core Android native directory symlink rejected")
    try:
        native_dir.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(
            "Secure Core Android native directory must be inside AOSP root"
        ) from exc
    if not native_dir.is_dir():
        raise ValueError("Secure Core Android native directory unavailable")

    android_bp, android_bp_sha = _read_build_source(
        native_dir / ANDROID_BP,
        label="Secure Core Android.bp",
    )
    rust_source, rust_sha = _read_build_source(
        native_dir / VERIFIED_SESSION_RUST,
        label="verified Secretkeeper Rust source",
    )

    if f'name: "{VERIFIED_SESSION_MODULE}"' not in android_bp:
        raise ValueError("verified Secretkeeper Soong module missing")
    required_markers = (
        "SkSession::new(sk, dice, Some(expected_sk_key))",
        "CoseKey::from_slice(expected_sk_key_cbor)",
        "use explicitkeydice::OwnedDiceArtifactsWithExplicitKey;",
    )
    for marker in required_markers:
        if marker not in rust_source:
            raise ValueError(
                f"verified Secretkeeper Rust source missing required marker: {marker}"
            )

    soong = root / SOONG_UI
    if soong.is_symlink():
        raise ValueError("Soong UI symlink rejected")
    if not soong.is_file():
        raise ValueError("Soong UI unavailable")

    command = [str(soong), "--make-mode", VERIFIED_SESSION_MODULE]
    command_sha = hashlib.sha256(
        "\x00".join(command).encode("utf-8")
    ).hexdigest()

    try:
        result = runner(command, cwd=root, timeout=timeout)
        returncode = int(result.returncode)
        stdout = result.stdout if isinstance(result.stdout, str) else ""
        stderr = result.stderr if isinstance(result.stderr, str) else ""
        reason = "soong-build-succeeded" if returncode == 0 else "soong-build-failed"
    except subprocess.TimeoutExpired as exc:
        returncode = -1
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        reason = "soong-build-timeout"
    except OSError as exc:
        returncode = -1
        stdout = ""
        stderr = f"{type(exc).__name__}:{exc}"
        reason = "soong-build-execution-error"

    return AospVerifiedSessionBuildReceipt(
        schema_version=AOSP_VERIFIED_SESSION_BUILD_SCHEMA_VERSION,
        source_target=ANDROID_SECURITY_17_R1.name,
        module_name=VERIFIED_SESSION_MODULE,
        secretkeeper_contract_receipt_sha256=contract.receipt_sha256,
        contract_lock_sha256=lock.lock_sha256,
        android_bp_sha256=android_bp_sha,
        rust_source_sha256=rust_sha,
        command_sha256=command_sha,
        stdout_sha256=hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
        returncode=returncode,
        build_succeeded=returncode == 0,
        reason=reason,
    )
