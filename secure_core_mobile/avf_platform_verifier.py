"""Composite AVF verifier with fail-closed platform provenance."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from .avf_certificate import verify_avf_leaf_claims
from .avf_policy import AvfComponentPolicy
from .cert_chain import CertificateTrustStore, verify_certificate_chain
from .platform_evidence import PlatformVerification, generic_crypto_result

@dataclass(frozen=True)
class AvfTrustProfile:
    certificate_store: CertificateTrustStore
    profile_version: int = 1
    def __post_init__(self):
        if self.profile_version <= 0: raise ValueError("AVF trust profile version must be positive")

class AndroidAvfAuthoritativeVerifierUnavailable:
    def verify(self,*args,**kwargs):
        raise RuntimeError("authoritative Android AVF/RKP verifier not implemented")

def verify_avf_platform(*,chain_der:tuple[bytes,...],challenge:bytes,component_policy:AvfComponentPolicy,trust_profile:AvfTrustProfile)->PlatformVerification:
    if not chain_der: raise ValueError("empty AVF certificate chain")
    verify_certificate_chain(chain_der,trust_profile.certificate_store)
    claims=verify_avf_leaf_claims(chain_der[0],expected_challenge=challenge)
    component_policy.verify(claims)
    evidence_sha=hashlib.sha256(b"".join(chain_der)).hexdigest()
    return generic_crypto_result(verified=True, evidence_sha256=evidence_sha)
