#include "avf_attestation_bridge.h"

#include <vm_payload.h>

#include <cstdlib>

namespace {

constexpr size_t kMaxChallengeBytes = 64;
constexpr size_t kMaxCertificates = 16;
constexpr size_t kMaxCertificateBytes = 64 * 1024;
constexpr size_t kMaxCertificateChainBytes = 512 * 1024;

struct AttestationResultGuard {
    AVmAttestationResult* value = nullptr;

    ~AttestationResultGuard() {
        if (value != nullptr) {
            AVmAttestationResult_free(value);
        }
    }

    AttestationResultGuard(const AttestationResultGuard&) = delete;
    AttestationResultGuard& operator=(const AttestationResultGuard&) = delete;
    AttestationResultGuard() = default;
};

int32_t map_attestation_status(AVmAttestationStatus status) {
    switch (status) {
        case ATTESTATION_OK:
            return SCM_AVF_BRIDGE_OK;
        case ATTESTATION_ERROR_INVALID_CHALLENGE:
            return SCM_AVF_BRIDGE_INVALID_CHALLENGE;
        case ATTESTATION_ERROR_UNSUPPORTED:
            return SCM_AVF_BRIDGE_UNSUPPORTED;
        case ATTESTATION_ERROR_ATTESTATION_FAILED:
        default:
            return SCM_AVF_BRIDGE_ATTESTATION_FAILED;
    }
}

void reset_chain(ScmAvfCertificateChain* chain) {
    if (chain == nullptr) {
        return;
    }
    chain->certificates = nullptr;
    chain->certificate_count = 0;
}

}  // namespace

extern "C" void scm_avf_free_certificate_chain(ScmAvfCertificateChain* chain) {
    if (chain == nullptr) {
        return;
    }
    if (chain->certificates != nullptr) {
        for (size_t index = 0; index < chain->certificate_count; ++index) {
            std::free(chain->certificates[index].data);
            chain->certificates[index].data = nullptr;
            chain->certificates[index].size = 0;
        }
        std::free(chain->certificates);
    }
    reset_chain(chain);
}

extern "C" int32_t scm_avf_request_attestation(
    const uint8_t* challenge,
    size_t challenge_size,
    ScmAvfCertificateChain* out_chain) {
    if (out_chain == nullptr) {
        return SCM_AVF_BRIDGE_INVALID_ARGUMENT;
    }
    reset_chain(out_chain);

    if (challenge == nullptr || challenge_size == 0 ||
        challenge_size > kMaxChallengeBytes) {
        return SCM_AVF_BRIDGE_INVALID_CHALLENGE;
    }

    AttestationResultGuard result;
    const AVmAttestationStatus platform_status =
        AVmPayload_requestAttestation(challenge, challenge_size, &result.value);
    const int32_t mapped_status = map_attestation_status(platform_status);
    if (mapped_status != SCM_AVF_BRIDGE_OK) {
        return mapped_status;
    }
    if (result.value == nullptr) {
        return SCM_AVF_BRIDGE_MALFORMED_RESULT;
    }

    const size_t certificate_count =
        AVmAttestationResult_getCertificateCount(result.value);
    if (certificate_count == 0) {
        return SCM_AVF_BRIDGE_MALFORMED_RESULT;
    }
    if (certificate_count > kMaxCertificates) {
        return SCM_AVF_BRIDGE_RESOURCE_LIMIT;
    }

    ScmAvfCertificateChain local{};
    local.certificates = static_cast<ScmAvfCertificate*>(
        std::calloc(certificate_count, sizeof(ScmAvfCertificate)));
    if (local.certificates == nullptr) {
        return SCM_AVF_BRIDGE_ALLOCATION_FAILED;
    }
    local.certificate_count = certificate_count;

    size_t total_bytes = 0;
    for (size_t index = 0; index < certificate_count; ++index) {
        const size_t certificate_size =
            AVmAttestationResult_getCertificateAt(
                result.value, index, nullptr, 0);
        if (certificate_size == 0) {
            scm_avf_free_certificate_chain(&local);
            return SCM_AVF_BRIDGE_MALFORMED_RESULT;
        }
        if (certificate_size > kMaxCertificateBytes ||
            total_bytes > kMaxCertificateChainBytes - certificate_size) {
            scm_avf_free_certificate_chain(&local);
            return SCM_AVF_BRIDGE_RESOURCE_LIMIT;
        }

        auto* certificate =
            static_cast<uint8_t*>(std::malloc(certificate_size));
        if (certificate == nullptr) {
            scm_avf_free_certificate_chain(&local);
            return SCM_AVF_BRIDGE_ALLOCATION_FAILED;
        }

        const size_t reported_size =
            AVmAttestationResult_getCertificateAt(
                result.value, index, certificate, certificate_size);
        if (reported_size != certificate_size) {
            std::free(certificate);
            scm_avf_free_certificate_chain(&local);
            return SCM_AVF_BRIDGE_MALFORMED_RESULT;
        }

        local.certificates[index].data = certificate;
        local.certificates[index].size = certificate_size;
        total_bytes += certificate_size;
    }

    *out_chain = local;
    return SCM_AVF_BRIDGE_OK;
}
