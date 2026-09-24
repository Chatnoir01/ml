#include "avf_profile_pin_bridge.h"

#include <cstddef>
#include <cstdint>

namespace {

constexpr int hex_value(char value) {
    if (value >= '0' && value <= '9') {
        return value - '0';
    }
    if (value >= 'a' && value <= 'f') {
        return value - 'a' + 10;
    }
    if (value >= 'A' && value <= 'F') {
        return value - 'A' + 10;
    }
    return -1;
}

#ifdef SCM_AVF_PROFILE_PIN_HEX
constexpr char kProvisionedProfilePin[] = SCM_AVF_PROFILE_PIN_HEX;
#endif

}  // namespace

extern "C" int32_t scm_avf_load_preprovisioned_profile_pin(
    uint8_t* out_pin,
    size_t out_pin_size) {
    if (out_pin == nullptr || out_pin_size != SCM_AVF_PROFILE_PIN_BYTES) {
        return SCM_AVF_PROFILE_PIN_INVALID_ARGUMENT;
    }

#ifndef SCM_AVF_PROFILE_PIN_HEX
    return SCM_AVF_PROFILE_PIN_NOT_PROVISIONED;
#else
    constexpr size_t kExpectedHexChars = SCM_AVF_PROFILE_PIN_BYTES * 2;
    if (sizeof(kProvisionedProfilePin) != kExpectedHexChars + 1) {
        return SCM_AVF_PROFILE_PIN_MALFORMED;
    }

    for (size_t index = 0; index < SCM_AVF_PROFILE_PIN_BYTES; ++index) {
        const int high = hex_value(kProvisionedProfilePin[index * 2]);
        const int low = hex_value(kProvisionedProfilePin[index * 2 + 1]);
        if (high < 0 || low < 0) {
            return SCM_AVF_PROFILE_PIN_MALFORMED;
        }
        out_pin[index] = static_cast<uint8_t>((high << 4) | low);
    }
    return SCM_AVF_PROFILE_PIN_OK;
#endif
}
