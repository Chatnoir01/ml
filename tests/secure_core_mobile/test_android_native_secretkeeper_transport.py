from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


BRIDGE_DIR = Path("secure_core_mobile/android_native")
SOURCE = BRIDGE_DIR / "secretkeeper_transport_bridge.cpp"
ANDROID_BP = BRIDGE_DIR / "Android.bp"


def test_secretkeeper_transport_bridge_compiles_and_enforces_bounds(
    tmp_path: Path,
) -> None:
    compiler = shutil.which("c++") or shutil.which("g++")
    if compiler is None:
        pytest.skip("host C++ compiler unavailable")

    harness = tmp_path / "transport_harness.cpp"
    harness.write_text(
        r"""
#include "secretkeeper_transport_bridge.h"

#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <cstring>

static int g_process_calls = 0;
static int g_free_calls = 0;
static int32_t g_platform_status = 0;
static size_t g_response_size = 4;
static bool g_return_null = false;

extern "C" int32_t process_packet(
    void*,
    const uint8_t* request,
    size_t request_size,
    uint8_t** out_response,
    size_t* out_response_size) {
    ++g_process_calls;
    assert(request != nullptr);
    assert(request_size > 0);

    if (g_return_null) {
        *out_response = nullptr;
        *out_response_size = 0;
        return g_platform_status;
    }

    uint8_t* response = static_cast<uint8_t*>(std::malloc(g_response_size));
    assert(response != nullptr);
    for (size_t i = 0; i < g_response_size; ++i) {
        response[i] = static_cast<uint8_t>(0xA0 + (i & 0x0F));
    }
    *out_response = response;
    *out_response_size = g_response_size;
    return g_platform_status;
}

extern "C" void free_packet(
    void*,
    uint8_t* response,
    size_t) {
    ++g_free_calls;
    std::free(response);
}

int main() {
    const uint8_t request[] = {1, 2, 3};
    ScmSecretkeeperTransport transport{
        nullptr,
        process_packet,
        free_packet,
    };
    ScmSecretkeeperPacket response{};

    assert(scm_secretkeeper_process_protected_packet(
        &transport,
        request,
        sizeof(request),
        &response) == SCM_SK_TRANSPORT_OK);
    assert(response.size == 4);
    assert(response.data[0] == 0xA0);
    assert(response.data[3] == 0xA3);
    assert(g_process_calls == 1);
    assert(g_free_calls == 1);
    scm_secretkeeper_free_packet(&response);
    assert(response.data == nullptr);
    assert(response.size == 0);

    const int calls_before_invalid = g_process_calls;
    assert(scm_secretkeeper_process_protected_packet(
        &transport,
        nullptr,
        0,
        &response) == SCM_SK_TRANSPORT_INVALID_ARGUMENT);
    assert(g_process_calls == calls_before_invalid);

    uint8_t* huge = static_cast<uint8_t*>(std::malloc((1024 * 1024) + 1));
    assert(huge != nullptr);
    assert(scm_secretkeeper_process_protected_packet(
        &transport,
        huge,
        (1024 * 1024) + 1,
        &response) == SCM_SK_TRANSPORT_REQUEST_TOO_LARGE);
    std::free(huge);
    assert(g_process_calls == calls_before_invalid);

    g_response_size = (1024 * 1024) + 1;
    assert(scm_secretkeeper_process_protected_packet(
        &transport,
        request,
        sizeof(request),
        &response) == SCM_SK_TRANSPORT_RESPONSE_TOO_LARGE);
    assert(g_free_calls == 2);

    g_response_size = 4;
    g_platform_status = -1;
    assert(scm_secretkeeper_process_protected_packet(
        &transport,
        request,
        sizeof(request),
        &response) == SCM_SK_TRANSPORT_PLATFORM_ERROR);
    assert(g_free_calls == 3);

    g_platform_status = 0;
    g_return_null = true;
    assert(scm_secretkeeper_process_protected_packet(
        &transport,
        request,
        sizeof(request),
        &response) == SCM_SK_TRANSPORT_MALFORMED_RESPONSE);
    assert(g_free_calls == 3);

    return 0;
}
""",
        encoding="utf-8",
    )

    binary = tmp_path / "transport-test"
    compiled = subprocess.run(
        [
            compiler,
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

    executed = subprocess.run(
        [str(binary)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert executed.returncode == 0, executed.stderr


def test_secretkeeper_transport_bridge_has_no_identity_or_plaintext_api() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    header = (BRIDGE_DIR / "secretkeeper_transport_bridge.h").read_text(
        encoding="utf-8"
    )

    forbidden = (
        "getSecretkeeperIdentity",
        "secretkeeper_public_key",
        "StoreSecret",
        "GetSecret",
        "plaintext",
        "secret_management_request",
    )
    for marker in forbidden:
        assert marker not in source
        assert marker not in header

    assert "process_protected_packet" in header
    assert "secretkeeper_transport_bridge.cpp" in ANDROID_BP.read_text(
        encoding="utf-8"
    )
