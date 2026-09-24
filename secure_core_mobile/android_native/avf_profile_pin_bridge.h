#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum ScmAvfProfilePinStatus {
    SCM_AVF_PROFILE_PIN_OK = 0,
    SCM_AVF_PROFILE_PIN_INVALID_ARGUMENT = -21001,
    SCM_AVF_PROFILE_PIN_NOT_PROVISIONED = -21002,
    SCM_AVF_PROFILE_PIN_MALFORMED = -21003,
};

enum {
    SCM_AVF_PROFILE_PIN_BYTES = 32,
};

int32_t scm_avf_load_preprovisioned_profile_pin(
    uint8_t* out_pin,
    size_t out_pin_size);

#ifdef __cplusplus
}
#endif
