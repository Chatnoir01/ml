// Android Binder transport for already-protected Secretkeeper packets.
//
// This FFI layer deliberately does not create AuthGraph sessions and does not
// accept plaintext SecretManagement requests. It forwards only opaque protected
// packet bytes to ISecretkeeper::processSecretManagementRequest.

use android_hardware_security_secretkeeper::aidl::android::hardware::security::secretkeeper::ISecretkeeper::ISecretkeeper;
use std::mem;
use std::ptr;

const SECRETKEEPER_DEFAULT_SERVICE: &str =
    "android.hardware.security.secretkeeper.ISecretkeeper/default";
const MAX_PACKET_BYTES: usize = 1024 * 1024;

pub const SCM_SK_BINDER_OK: i32 = 0;
pub const SCM_SK_BINDER_INVALID_ARGUMENT: i32 = -23001;
pub const SCM_SK_BINDER_SERVICE_UNAVAILABLE: i32 = -23002;
pub const SCM_SK_BINDER_CALL_FAILED: i32 = -23003;
pub const SCM_SK_BINDER_MALFORMED_RESPONSE: i32 = -23004;
pub const SCM_SK_BINDER_RESOURCE_LIMIT: i32 = -23005;

#[repr(C)]
pub struct ScmSecretkeeperBinderPacket {
    pub data: *mut u8,
    pub size: usize,
}

fn reset_packet(packet: *mut ScmSecretkeeperBinderPacket) {
    if packet.is_null() {
        return;
    }
    // SAFETY: caller supplied a non-null output pointer owned by this call.
    unsafe {
        (*packet).data = ptr::null_mut();
        (*packet).size = 0;
    }
}

#[no_mangle]
pub extern "C" fn scm_secretkeeper_binder_free_packet(
    packet: *mut ScmSecretkeeperBinderPacket,
) {
    if packet.is_null() {
        return;
    }

    // SAFETY: buffers returned by scm_secretkeeper_binder_process are allocated
    // as boxed slices and ownership is transferred back exactly once here.
    unsafe {
        let data = (*packet).data;
        let size = (*packet).size;
        if !data.is_null() && size != 0 {
            let slice = ptr::slice_from_raw_parts_mut(data, size);
            drop(Box::from_raw(slice));
        }
        (*packet).data = ptr::null_mut();
        (*packet).size = 0;
    }
}

#[no_mangle]
pub extern "C" fn scm_secretkeeper_binder_process(
    request: *const u8,
    request_size: usize,
    out_response: *mut ScmSecretkeeperBinderPacket,
) -> i32 {
    if out_response.is_null() {
        return SCM_SK_BINDER_INVALID_ARGUMENT;
    }
    reset_packet(out_response);

    if request.is_null() || request_size == 0 {
        return SCM_SK_BINDER_INVALID_ARGUMENT;
    }
    if request_size > MAX_PACKET_BYTES {
        return SCM_SK_BINDER_RESOURCE_LIMIT;
    }

    // SAFETY: request was checked non-null and length is bounded above.
    let request_bytes = unsafe { std::slice::from_raw_parts(request, request_size) };

    let service: binder::Strong<dyn ISecretkeeper> =
        match binder::get_interface(SECRETKEEPER_DEFAULT_SERVICE) {
            Ok(service) => service,
            Err(_) => return SCM_SK_BINDER_SERVICE_UNAVAILABLE,
        };

    let response = match service.processSecretManagementRequest(request_bytes) {
        Ok(response) => response,
        Err(_) => return SCM_SK_BINDER_CALL_FAILED,
    };

    if response.is_empty() {
        return SCM_SK_BINDER_MALFORMED_RESPONSE;
    }
    if response.len() > MAX_PACKET_BYTES {
        return SCM_SK_BINDER_RESOURCE_LIMIT;
    }

    let mut boxed = response.into_boxed_slice();
    let size = boxed.len();
    let data = boxed.as_mut_ptr();
    mem::forget(boxed);

    // SAFETY: out_response is non-null and receives ownership of boxed bytes.
    unsafe {
        (*out_response).data = data;
        (*out_response).size = size;
    }
    SCM_SK_BINDER_OK
}
