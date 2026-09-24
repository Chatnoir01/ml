#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum ScmAvfBridgeStatus {
    SCM_AVF_BRIDGE_OK = 0,
    SCM_AVF_BRIDGE_INVALID_ARGUMENT = -20001,
    SCM_AVF_BRIDGE_INVALID_CHALLENGE = -20002,
    SCM_AVF_BRIDGE_UNSUPPORTED = -20003,
    SCM_AVF_BRIDGE_ATTESTATION_FAILED = -20004,
    SCM_AVF_BRIDGE_MALFORMED_RESULT = -20005,
    SCM_AVF_BRIDGE_RESOURCE_LIMIT = -20006,
    SCM_AVF_BRIDGE_ALLOCATION_FAILED = -20007,
};

typedef struct ScmAvfCertificate {
    uint8_t* data;
    size_t size;
} ScmAvfCertificate;

typedef struct ScmAvfCertificateChain {
    ScmAvfCertificate* certificates;
    size_t certificate_count;
} ScmAvfCertificateChain;

int32_t scm_avf_request_attestation(
    const uint8_t* challenge,
    size_t challenge_size,
    ScmAvfCertificateChain* out_chain);

void scm_avf_free_certificate_chain(ScmAvfCertificateChain* chain);

#ifdef __cplusplus
}
#endif
