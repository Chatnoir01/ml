"""Safe staging of Secure Core Android-native sources into an AOSP checkout.

This copies an exact allowlisted source set into
external/secure_core/android_native. It prevalidates the full operation before
writing anything, rejects symlinks and unexpected files, and requires explicit
permission before replacing different existing content.

Staging is not a build and does not establish any platform trust property.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile


AOSP_NATIVE_STAGING_SCHEMA_VERSION = 1
AOSP_NATIVE_DESTINATION = Path("external/secure_core/android_native")
MAX_NATIVE_FILE_BYTES = 4 * 1024 * 1024

NATIVE_SOURCE_FILES = (
    "Android.bp",
    "avf_attestation_bridge.cpp",
    "avf_attestation_bridge.h",
    "avf_profile_pin_bridge.cpp",
    "avf_profile_pin_bridge.h",
    "rollback_protected_secret_bridge.cpp",
    "rollback_protected_secret_bridge.h",
    "secretkeeper_binder_bridge.rs",
    "secretkeeper_transport_bridge.cpp",
    "secretkeeper_transport_bridge.h",
    "secretkeeper_verified_session.rs",
)


@dataclass(frozen=True)
class StagedNativeFile:
    name: str
    sha256: str
    size: int


@dataclass(frozen=True)
class AospNativeStagingReceipt:
    schema_version: int
    destination: str
    file_count: int
    files: tuple[StagedNativeFile, ...]
    replaced_existing: bool

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            asdict(self),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

    @property
    def receipt_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _read_regular_file(path: Path, *, label: str) -> bytes:
    if path.is_symlink():
        raise ValueError(f"{label} symlink rejected")
    if not path.is_file():
        raise ValueError(f"{label} unavailable")
    size = path.stat().st_size
    if size <= 0 or size > MAX_NATIVE_FILE_BYTES:
        raise ValueError(f"{label} size invalid")
    return path.read_bytes()


def stage_android_native_sources(
    *,
    aosp_root: Path | str,
    source_native_dir: Path | str,
    replace_existing: bool = False,
) -> AospNativeStagingReceipt:
    root = Path(aosp_root)
    if root.is_symlink():
        raise ValueError("AOSP root symlink rejected")
    if not root.is_dir():
        raise ValueError("AOSP root unavailable")
    soong = root / "build/soong/soong_ui.bash"
    if soong.is_symlink() or not soong.is_file():
        raise ValueError("AOSP Soong UI unavailable")

    source = Path(source_native_dir)
    if source.is_symlink():
        raise ValueError("Secure Core native source directory symlink rejected")
    if not source.is_dir():
        raise ValueError("Secure Core native source directory unavailable")

    actual_source_names = {
        path.name for path in source.iterdir()
        if path.is_file() or path.is_symlink()
    }
    expected_names = set(NATIVE_SOURCE_FILES)
    if actual_source_names != expected_names:
        missing = sorted(expected_names - actual_source_names)
        extra = sorted(actual_source_names - expected_names)
        raise ValueError(
            f"native source set mismatch: missing={missing}, extra={extra}"
        )

    source_bytes: dict[str, bytes] = {}
    staged: list[StagedNativeFile] = []
    for name in NATIVE_SOURCE_FILES:
        data = _read_regular_file(
            source / name,
            label=f"native source {name}",
        )
        source_bytes[name] = data
        staged.append(
            StagedNativeFile(
                name=name,
                sha256=hashlib.sha256(data).hexdigest(),
                size=len(data),
            )
        )

    destination = root / AOSP_NATIVE_DESTINATION
    if destination.is_symlink():
        raise ValueError("AOSP native destination symlink rejected")
    if destination.exists() and not destination.is_dir():
        raise ValueError("AOSP native destination is not a directory")

    if destination.is_dir():
        existing_names = {
            path.name for path in destination.iterdir()
            if path.is_file() or path.is_symlink()
        }
        unexpected = sorted(existing_names - expected_names)
        if unexpected:
            raise ValueError(
                f"unexpected files in AOSP native destination: {unexpected}"
            )

        for name in NATIVE_SOURCE_FILES:
            target = destination / name
            if not target.exists() and not target.is_symlink():
                continue
            if target.is_symlink():
                raise ValueError(f"AOSP destination symlink rejected: {name}")
            if not target.is_file():
                raise ValueError(f"AOSP destination entry is not a file: {name}")
            current = target.read_bytes()
            if current != source_bytes[name] and not replace_existing:
                raise ValueError(
                    f"AOSP native file differs; explicit replacement required: {name}"
                )

    destination.mkdir(parents=True, exist_ok=True)

    for name in NATIVE_SOURCE_FILES:
        target = destination / name
        data = source_bytes[name]
        if target.is_file() and target.read_bytes() == data:
            continue

        fd, temp_name = tempfile.mkstemp(
            prefix=f".{name}.",
            dir=str(destination),
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    return AospNativeStagingReceipt(
        schema_version=AOSP_NATIVE_STAGING_SCHEMA_VERSION,
        destination=AOSP_NATIVE_DESTINATION.as_posix(),
        file_count=len(staged),
        files=tuple(staged),
        replaced_existing=bool(replace_existing),
    )
