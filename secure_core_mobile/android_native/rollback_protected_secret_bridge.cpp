#include "rollback_protected_secret_bridge.h"

#include <vm_payload.h>

namespace {

int32_t map_vm_payload_status(int32_t status) {
    switch (status) {
        case AVMACCESSROLLBACKPROTECTEDSECRETSTATUS_ENTRY_NOT_FOUND:
            return SCM_RP_NOT_FOUND;
        case AVMACCESSROLLBACKPROTECTEDSECRETSTATUS_BAD_SIZE:
            return SCM_RP_BAD_SIZE;
        case AVMACCESSROLLBACKPROTECTEDSECRETSTATUS_ACCESS_FAILED:
            return SCM_RP_ACCESS_FAILED;
        default:
            return SCM_RP_MALFORMED_RESULT;
    }
}

}  // namespace

extern "C" int32_t scm_avf_write_rollback_protected_secret(
    const uint8_t* data,
    size_t size) {
    if (data == nullptr || size != SCM_RP_SECRET_BYTES) {
        return SCM_RP_INVALID_ARGUMENT;
    }

    const int32_t result =
        AVmPayload_writeRollbackProtectedSecret(data, size);
    if (result < 0) {
        return map_vm_payload_status(result);
    }
    if (result != static_cast<int32_t>(SCM_RP_SECRET_BYTES)) {
        return SCM_RP_MALFORMED_RESULT;
    }
    return SCM_RP_OK;
}

extern "C" int32_t scm_avf_read_rollback_protected_secret(
    uint8_t* out_data,
    size_t size) {
    if (out_data == nullptr || size != SCM_RP_SECRET_BYTES) {
        return SCM_RP_INVALID_ARGUMENT;
    }

    const int32_t result =
        AVmPayload_readRollbackProtectedSecret(out_data, size);
    if (result < 0) {
        return map_vm_payload_status(result);
    }
    if (result != static_cast<int32_t>(SCM_RP_SECRET_BYTES)) {
        return SCM_RP_MALFORMED_RESULT;
    }
    return SCM_RP_OK;
}
