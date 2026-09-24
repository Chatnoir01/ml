from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


BRIDGE_DIR = Path("secure_core_mobile/android_native")
SOURCE = BRIDGE_DIR / "avf_attestation_bridge.cpp"
ANDROID_BP = BRIDGE_DIR / "Android.bp"


def test_native_bridge_uses_attestation_chain_api_without_exporting_private_key() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "AVmPayload_requestAttestation" in source
    assert "AVmAttestationResult_getCertificateCount" in source
    assert "AVmAttestationResult_getCertificateAt" in source
    assert "AVmAttestationResult_free" in source
    assert "AVmAttestationResult_getPrivateKey" not in source
    assert "AVmAttestationResult_sign" not in source
    assert 'shared_libs: ["libvm_payload#current"]' in ANDROID_BP.read_text(encoding="utf-8")


def test_native_bridge_compiles_and_enforces_memory_contract(tmp_path: Path) -> None:
    compiler = shutil.which("c++") or shutil.which("g++")
    if compiler is None:
        pytest.skip("host C++ compiler unavailable")

    (tmp_path / "vm_payload.h").write_text(
        r"""
#pragma once
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct AVmAttestationResult AVmAttestationResult;
typedef enum AVmAttestationStatus : int32_t {
    ATTESTATION_OK = 0,
    ATTESTATION_ERROR_INVALID_CHALLENGE = -10001,
    ATTESTATION_ERROR_ATTESTATION_FAILED = -10002,
    ATTESTATION_ERROR_UNSUPPORTED = -10003,
} AVmAttestationStatus;
AVmAttestationStatus AVmPayload_requestAttestation(
    const void* challenge, size_t challenge_size, AVmAttestationResult** result);
size_t AVmAttestationResult_getCertificateCount(const AVmAttestationResult* result);
size_t AVmAttestationResult_getCertificateAt(
    const AVmAttestationResult* result, size_t index, void* data, size_t size);
void AVmAttestationResult_free(AVmAttestationResult* result);
#ifdef __cplusplus
}
#endif
""",
        encoding="utf-8",
    )

    harness = tmp_path / "harness.cpp"
    harness.write_text(
        r"""
#include "avf_attestation_bridge.h"
#include <vm_payload.h>
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <vector>

struct AVmAttestationResult {
    std::vector<std::vector<uint8_t>> certificates;
};

static AVmAttestationStatus g_status = ATTESTATION_OK;
static size_t g_free_count = 0;
static size_t g_request_count = 0;
static bool g_oversized_count = false;

extern "C" AVmAttestationStatus AVmPayload_requestAttestation(
    const void* challenge, size_t challenge_size, AVmAttestationResult** result) {
    ++g_request_count;
    assert(challenge != nullptr);
    assert(challenge_size > 0);
    if (g_status != ATTESTATION_OK) {
        *result = nullptr;
        return g_status;
    }
    auto* value = new AVmAttestationResult();
    value->certificates = {{0x30, 0x01, 0x01}, {0x30, 0x02, 0x02, 0x03}};
    *result = value;
    return ATTESTATION_OK;
}

extern "C" size_t AVmAttestationResult_getCertificateCount(
    const AVmAttestationResult* result) {
    return g_oversized_count ? 17 : result->certificates.size();
}

extern "C" size_t AVmAttestationResult_getCertificateAt(
    const AVmAttestationResult* result, size_t index, void* data, size_t size) {
    const auto& cert = result->certificates.at(index);
    if (data != nullptr && size != 0) {
        std::memcpy(data, cert.data(), std::min(size, cert.size()));
    }
    return cert.size();
}

extern "C" void AVmAttestationResult_free(AVmAttestationResult* result) {
    ++g_free_count;
    delete result;
}

int main() {
    const uint8_t challenge[] = {1, 2, 3, 4};
    ScmAvfCertificateChain chain{};

    assert(scm_avf_request_attestation(
        challenge, sizeof(challenge), &chain) == SCM_AVF_BRIDGE_OK);
    assert(chain.certificate_count == 2);
    assert(chain.certificates[0].size == 3);
    assert(chain.certificates[1].size == 4);
    assert(g_free_count == 1);
    scm_avf_free_certificate_chain(&chain);
    assert(chain.certificates == nullptr);
    assert(chain.certificate_count == 0);

    const size_t requests_before_invalid = g_request_count;
    assert(scm_avf_request_attestation(
        nullptr, 0, &chain) == SCM_AVF_BRIDGE_INVALID_CHALLENGE);
    assert(g_request_count == requests_before_invalid);

    g_status = ATTESTATION_ERROR_UNSUPPORTED;
    assert(scm_avf_request_attestation(
        challenge, sizeof(challenge), &chain) == SCM_AVF_BRIDGE_UNSUPPORTED);
    assert(g_free_count == 1);

    g_status = ATTESTATION_OK;
    g_oversized_count = true;
    assert(scm_avf_request_attestation(
        challenge, sizeof(challenge), &chain) == SCM_AVF_BRIDGE_RESOURCE_LIMIT);
    assert(g_free_count == 2);
    return 0;
}
""",
        encoding="utf-8",
    )

    binary = tmp_path / "bridge-test"
    compiled = subprocess.run(
        [
            compiler,
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(tmp_path),
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
