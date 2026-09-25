from __future__ import annotations

from pathlib import Path

import pytest

from secure_core_mobile.aosp_native_staging import (
    AOSP_NATIVE_DESTINATION,
    NATIVE_SOURCE_FILES,
    stage_android_native_sources,
)


def _aosp(tmp_path: Path) -> Path:
    root = tmp_path / "aosp"
    soong = root / "build/soong/soong_ui.bash"
    soong.parent.mkdir(parents=True)
    soong.write_text("#!/bin/sh\n", encoding="utf-8")
    return root


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "native"
    source.mkdir()
    for name in NATIVE_SOURCE_FILES:
        (source / name).write_text(f"content:{name}\n", encoding="utf-8")
    return source


def test_native_staging_copies_exact_allowlist_and_is_idempotent(tmp_path: Path) -> None:
    root = _aosp(tmp_path)
    source = _source(tmp_path)

    first = stage_android_native_sources(
        aosp_root=root,
        source_native_dir=source,
    )
    second = stage_android_native_sources(
        aosp_root=root,
        source_native_dir=source,
    )

    destination = root / AOSP_NATIVE_DESTINATION
    assert first.file_count == len(NATIVE_SOURCE_FILES)
    assert first.receipt_sha256 == second.receipt_sha256
    assert sorted(path.name for path in destination.iterdir()) == sorted(
        NATIVE_SOURCE_FILES
    )
    assert all(len(item.sha256) == 64 for item in first.files)


def test_different_existing_file_requires_explicit_replacement(tmp_path: Path) -> None:
    root = _aosp(tmp_path)
    source = _source(tmp_path)
    stage_android_native_sources(
        aosp_root=root,
        source_native_dir=source,
    )

    target = root / AOSP_NATIVE_DESTINATION / "Android.bp"
    target.write_text("local-modification\n", encoding="utf-8")

    with pytest.raises(ValueError, match="explicit replacement required"):
        stage_android_native_sources(
            aosp_root=root,
            source_native_dir=source,
        )

    receipt = stage_android_native_sources(
        aosp_root=root,
        source_native_dir=source,
        replace_existing=True,
    )
    assert receipt.replaced_existing is True
    assert target.read_text(encoding="utf-8") == "content:Android.bp\n"


def test_unexpected_source_file_is_rejected(tmp_path: Path) -> None:
    root = _aosp(tmp_path)
    source = _source(tmp_path)
    (source / "unreviewed.rs").write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="source set mismatch"):
        stage_android_native_sources(
            aosp_root=root,
            source_native_dir=source,
        )


def test_unexpected_destination_file_is_rejected(tmp_path: Path) -> None:
    root = _aosp(tmp_path)
    source = _source(tmp_path)
    destination = root / AOSP_NATIVE_DESTINATION
    destination.mkdir(parents=True)
    (destination / "attacker.rs").write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="unexpected files"):
        stage_android_native_sources(
            aosp_root=root,
            source_native_dir=source,
        )


def test_destination_symlink_is_rejected(tmp_path: Path) -> None:
    root = _aosp(tmp_path)
    source = _source(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    destination = root / AOSP_NATIVE_DESTINATION
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="destination symlink"):
        stage_android_native_sources(
            aosp_root=root,
            source_native_dir=source,
        )


def test_source_file_symlink_is_rejected(tmp_path: Path) -> None:
    root = _aosp(tmp_path)
    source = _source(tmp_path)
    target = source / "real.rs"
    target.write_text("x", encoding="utf-8")
    victim = source / "secretkeeper_verified_session.rs"
    victim.unlink()
    victim.symlink_to(target)

    with pytest.raises(ValueError, match="symlink"):
        stage_android_native_sources(
            aosp_root=root,
            source_native_dir=source,
        )
