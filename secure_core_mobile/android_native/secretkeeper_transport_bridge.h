#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum ScmSecretkeeperTransportStatus {
    SCM_SK_TRANSPORT_OK = 0,
    SCM_SK_TRANSPORT_INVALID_ARGUMENT = -22001,
    SCM_SK_TRANSPORT_REQUEST_TOO_LARGE = -22002,
    SCM_SK_TRANSPORT_RESPONSE_TOO_LARGE = -22003,
    SCM_SK_TRANSPORT_PLATFORM_ERROR = -22004,
    SCM_SK_TRANSPORT_MALFORMED_RESPONSE = -22005,
    SCM_SK_TRANSPORT_ALLOCATION_FAILED = -22006,
};

typedef int32_t (*ScmSecretkeeperProcessProtectedPacketFn)(
    void* context,
    const uint8_t* request,
    size_t request_size,
    uint8_t** out_response,
    size_t* out_response_size);

typedef void (*ScmSecretkeeperFreeResponseFn)(
    void* context,
    uint8_t* response,
    size_t response_size);

typedef struct ScmSecretkeeperTransport {
    void* context;
    ScmSecretkeeperProcessProtectedPacketFn process_protected_packet;
    ScmSecretkeeperFreeResponseFn free_response;
} ScmSecretkeeperTransport;

typedef struct ScmSecretkeeperPacket {
    uint8_t* data;
    size_t size;
} ScmSecretkeeperPacket;

int32_t scm_secretkeeper_process_protected_packet(
    const ScmSecretkeeperTransport* transport,
    const uint8_t* request,
    size_t request_size,
    ScmSecretkeeperPacket* out_response);

void scm_secretkeeper_free_packet(ScmSecretkeeperPacket* packet);

#ifdef __cplusplus
}
#endif
