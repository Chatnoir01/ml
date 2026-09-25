// Verified Secretkeeper session wrapper for AOSP/system-side integration.
//
// This module deliberately has no constructor that omits expected_sk_key.
// The caller must supply the Secretkeeper identity obtained from the separately
// verified pvmfw/AVF path. AOSP SkSession then performs AuthGraph and checks the
// peer identity before the session is usable.

use android_hardware_security_secretkeeper::aidl::android::hardware::security::secretkeeper::
    ISecretkeeper::ISecretkeeper;
use coset::{CborSerializable, CoseKey};
use explicitkeydice::OwnedDiceArtifactsWithExplicitKey;
use secretkeeper_client::{Error as SkError, SkSession};
use std::fmt;

#[derive(Debug)]
pub enum VerifiedSkSessionError {
    EmptyExpectedIdentity,
    EmptyRequest,
    InvalidExpectedIdentity(coset::CoseError),
    Session(SkError),
}

impl fmt::Display for VerifiedSkSessionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyExpectedIdentity => {
                write!(f, "expected Secretkeeper identity must not be empty")
            }
            Self::EmptyRequest => {
                write!(f, "SecretManagement request must not be empty")
            }
            Self::InvalidExpectedIdentity(error) => {
                write!(f, "invalid expected Secretkeeper COSE identity: {error:?}")
            }
            Self::Session(error) => {
                write!(f, "Secretkeeper verified session failed: {error}")
            }
        }
    }
}

impl std::error::Error for VerifiedSkSessionError {}

pub struct VerifiedSkSession {
    inner: SkSession,
}

impl VerifiedSkSession {
    /// Establish AuthGraph while requiring the exact expected Secretkeeper key.
    ///
    /// There is intentionally no unverified constructor in this wrapper.
    pub fn new(
        sk: binder::Strong<dyn ISecretkeeper>,
        dice: &OwnedDiceArtifactsWithExplicitKey,
        expected_sk_key_cbor: &[u8],
    ) -> Result<Self, VerifiedSkSessionError> {
        if expected_sk_key_cbor.is_empty() {
            return Err(VerifiedSkSessionError::EmptyExpectedIdentity);
        }

        let expected_sk_key = CoseKey::from_slice(expected_sk_key_cbor)
            .map_err(VerifiedSkSessionError::InvalidExpectedIdentity)?;

        let inner = SkSession::new(sk, dice, Some(expected_sk_key))
            .map_err(VerifiedSkSessionError::Session)?;

        Ok(Self { inner })
    }

    /// Send one plaintext SecretManagement request through the AuthGraph-
    /// protected AOSP SkSession.
    pub fn secret_management_request(
        &mut self,
        request: &[u8],
    ) -> Result<Vec<u8>, VerifiedSkSessionError> {
        if request.is_empty() {
            return Err(VerifiedSkSessionError::EmptyRequest);
        }

        self.inner
            .secret_management_request(request)
            .map_err(VerifiedSkSessionError::Session)
    }

    /// Session identifier is exposed for transcript binding only.
    /// AES session keys remain encapsulated inside AOSP SkSession.
    pub fn session_id(&self) -> &[u8] {
        self.inner.session_id()
    }
}
