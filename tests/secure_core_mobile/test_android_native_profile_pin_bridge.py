from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


BRIDGE_DIR = Path("secure_core_mobile/android_native")
SOURCE = BRIDGE_DIR / "avf_profile_pin_bridge.cpp"
HEADER = BRIDGE_DIR / "avf_profile_pin_bridge.h"
ANDROID_BP = BRIDGE_DIR / "Android.bp"


def _compiler() -> str:
    compiler = shutil.which("c++") or shutil.which("g++")
    if compiler is None:
        pytest.skip("host C++ compiler unavailable")
    return compiler


def _compile(
    tmp_path: Path,
    *,
    macro: str | None,
) -> Path:
    harness = tmp_path / "pin_harness.cpp"
    harness.write_text(
        r"""
#include "avf_profile_pin_bridge.h"

#include <cassert>
#include <cstddef>
#include <cstdint>

#ifndef EXPECT_STATUS
#define EXPECT_STATUS SCM_AVF_PROFILE_PIN_NOT_PROVISIONED
#endif

int main() {
    uint8_t pin[SCM_AVF_PROFILE_PIN_BYTES];
    for (size_t i = 0; i < SCM_AVF_PROFILE_PIN_BYTES; ++i) {
        pin[i] = 0xCC;
    }
    assert(scm_avf_load_preprovisioned_profile_pin(
        nullptr, SCM_AVF_PROFILE_PIN_BYTES) == SCM_AVF_PROFILE_PIN_INVALID_ARGUMENT);
    assert(scm_avf_load_preprovisioned_profile_pin(
        pin, SCM_AVF_PROFILE_PIN_BYTES - 1) == SCM_AVF_PROFILE_PIN_INVALID_ARGUMENT);

    const int32_t status = scm_avf_load_preprovisioned_profile_pin(
        pin, SCM_AVF_PROFILE_PIN_BYTES);
    assert(status == EXPECT_STATUS);

#if EXPECT_STATUS != SCM_AVF_PROFILE_PIN_OK
    for (size_t i = 0; i < SCM_AVF_PROFILE_PIN_BYTES; ++i) {
        assert(pin[i] == 0);
    }
#endif

#ifdef EXPECT_FIRST_BYTE
    assert(pin[0] == EXPECT_FIRST_BYTE);
    assert(pin[31] == EXPECT_LAST_BYTE);
#endif
    return 0;
}
""",
        encoding="utf-8",
    )

    binary = tmp_path / "pin-bridge-test"
    command = [
        _compiler(),
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-I",
        str(BRIDGE_DIR),
        str(SOURCE),
        str(harness),
        "-o",
        str(binary),
    ]
    if macro is not None:
        command.insert(1, f'-DSCM_AVF_PROFILE_PIN_HEX="{macro}"')

    return_code = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )
    assert return_code.returncode == 0, return_code.stderr
    return binary


def test_native_pin_bridge_is_fail_closed_without_provisioning(tmp_path: Path) -> None:
    binary = _compile(tmp_path, macro=None)
    result = subprocess.run(
        [str(binary)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_native_pin_bridge_decodes_exact_compiled_profile_pin(tmp_path: Path) -> None:
    macro = "00" + ("ab" * 30) + "ff"
    harness = tmp_path / "pin_harness.cpp"
    harness.write_text(
        r"""
#include "avf_profile_pin_bridge.h"

#include <cassert>
#include <cstdint>

int main() {
    uint8_t pin[SCM_AVF_PROFILE_PIN_BYTES] = {};
    assert(scm_avf_load_preprovisioned_profile_pin(
        pin, sizeof(pin)) == SCM_AVF_PROFILE_PIN_OK);
    assert(pin[0] == 0x00);
    assert(pin[1] == 0xab);
    assert(pin[30] == 0xab);
    assert(pin[31] == 0xff);
    return 0;
}
""",
        encoding="utf-8",
    )
    binary = tmp_path / "pin-valid"
    compiled = subprocess.run(
        [
            _compiler(),
            f'-DSCM_AVF_PROFILE_PIN_HEX="{macro}"',
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(BRIDGE_DIR),
            str(SOURCE),
            str(harness),
            "-o",
            str(binary),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert compiled.returncode == 0, compiled.stderr
    executed = subprocess.run([str(binary)], capture_output=True, text=True, check=False)
    assert executed.returncode == 0, executed.stderr


@pytest.mark.parametrize(
    "macro",
    [
        "ab" * 31,
        "ab" * 33,
        ("ab" * 31) + "zz",
    ],
)
def test_native_pin_bridge_rejects_malformed_build_pin(
    tmp_path: Path,
    macro: str,
) -> None:
    harness = tmp_path / "pin_harness.cpp"
    harness.write_text(
        r"""
#include "avf_profile_pin_bridge.h"

#include <cassert>
#include <cstdint>

int main() {
    uint8_t pin[SCM_AVF_PROFILE_PIN_BYTES];
    for (size_t i = 0; i < SCM_AVF_PROFILE_PIN_BYTES; ++i) {
        pin[i] = 0xCC;
    }
    assert(scm_avf_load_preprovisioned_profile_pin(
        pin, sizeof(pin)) == SCM_AVF_PROFILE_PIN_MALFORMED);
    for (size_t i = 0; i < SCM_AVF_PROFILE_PIN_BYTES; ++i) {
        assert(pin[i] == 0);
    }
    return 0;
}
""",
        encoding="utf-8",
    )
    binary = tmp_path / "pin-malformed"
    compiled = subprocess.run(
        [
            _compiler(),
            f'-DSCM_AVF_PROFILE_PIN_HEX="{macro}"',
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(BRIDGE_DIR),
            str(SOURCE),
            str(harness),
            "-o",
            str(binary),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert compiled.returncode == 0, compiled.stderr
    executed = subprocess.run([str(binary)], capture_output=True, text=True, check=False)
    assert executed.returncode == 0, executed.stderr


def test_native_pin_bridge_has_no_mutable_host_runtime_source() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "getenv(",
        "std::getenv",
        "fopen(",
        "open(",
        "ifstream",
        "/data/",
        "/sdcard/",
        "/system/",
    )
    for marker in forbidden:
        assert marker not in source

    android_bp = ANDROID_BP.read_text(encoding="utf-8")
    assert "avf_profile_pin_bridge.cpp" in android_bp
    assert "SCM_AVF_PROFILE_PIN_HEX" in android_bp
