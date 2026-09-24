#include "secretkeeper_transport_bridge.h"

#include <cstdlib>
#include <cstring>

namespace {

constexpr size_t kMaxProtectedPacketBytes = 1024 * 1024;

void reset_packet(ScmSecretkeeperPacket* packet) {
    if (packet == nullptr) {
        return;
    }
    packet->data = nullptr;
    packet->size = 0;
}

}  // namespace

extern "C" void scm_secretkeeper_free_packet(ScmSecretkeeperPacket* packet) {
    if (packet == nullptr) {
        return;
    }
    std::free(packet->data);
    reset_packet(packet);
}

extern "C" int32_t scm_secretkeeper_process_protected_packet(
    const ScmSecretkeeperTransport* transport,
    const uint8_t* request,
    size_t request_size,
    ScmSecretkeeperPacket* out_response) {
    if (out_response == nullptr) {
        return SCM_SK_TRANSPORT_INVALID_ARGUMENT;
    }
    reset_packet(out_response);

    if (transport == nullptr ||
        transport->process_protected_packet == nullptr ||
        transport->free_response == nullptr ||
        request == nullptr ||
        request_size == 0) {
        return SCM_SK_TRANSPORT_INVALID_ARGUMENT;
    }
    if (request_size > kMaxProtectedPacketBytes) {
        return SCM_SK_TRANSPORT_REQUEST_TOO_LARGE;
    }

    uint8_t* platform_response = nullptr;
    size_t platform_response_size = 0;
    const int32_t platform_status = transport->process_protected_packet(
        transport->context,
        request,
        request_size,
        &platform_response,
        &platform_response_size);
    if (platform_status != 0) {
        if (platform_response != nullptr || platform_response_size != 0) {
            transport->free_response(
                transport->context,
                platform_response,
                platform_response_size);
        }
        return SCM_SK_TRANSPORT_PLATFORM_ERROR;
    }

    if (platform_response == nullptr || platform_response_size == 0) {
        if (platform_response != nullptr) {
            transport->free_response(
                transport->context,
                platform_response,
                platform_response_size);
        }
        return SCM_SK_TRANSPORT_MALFORMED_RESPONSE;
    }
    if (platform_response_size > kMaxProtectedPacketBytes) {
        transport->free_response(
            transport->context,
            platform_response,
            platform_response_size);
        return SCM_SK_TRANSPORT_RESPONSE_TOO_LARGE;
    }

    auto* copied = static_cast<uint8_t*>(std::malloc(platform_response_size));
    if (copied == nullptr) {
        transport->free_response(
            transport->context,
            platform_response,
            platform_response_size);
        return SCM_SK_TRANSPORT_ALLOCATION_FAILED;
    }
    std::memcpy(copied, platform_response, platform_response_size);

    transport->free_response(
        transport->context,
        platform_response,
        platform_response_size);

    out_response->data = copied;
    out_response->size = platform_response_size;
    return SCM_SK_TRANSPORT_OK;
}
