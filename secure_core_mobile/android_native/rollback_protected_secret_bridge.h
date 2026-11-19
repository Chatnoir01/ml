#pragma once

#include <cstddef>
#include <cstdint>

#ifdef __cplusplus
extern "C" {
#endif

enum ScmRollbackProtectedStatus : int32_t {
    SCM_RP_OK = 0,
    SCM_RP_NOT_FOUND = -24001,
    SCM_RP_BAD_SIZE = -24002,
    SCM_RP_ACCESS_FAILED = -24003,
    SCM_RP_INVALID_ARGUMENT = -24004,
    SCM_RP_MALFORMED_RESULT = -24005,
};

static constexpr size_t SCM_RP_SECRET_BYTES = 32;

int32_t scm_avf_write_rollback_protected_secret(
    const uint8_t* data,
    size_t size);

int32_t scm_avf_read_rollback_protected_secret(
    uint8_t* out_data,
    size_t size);

#ifdef __cplusplus
}
#endif
