# Android AVF / pVM integration boundary

Status: EXPERIMENTAL — platform integration not yet proven.

## Platform facts used by this design

Android AVF supports protected VMs (pVMs). Android 15 introduced VM remote
attestation so a client can establish that it is communicating with the
intended VM/software stack on a trusted device. Android attestation systems
also distinguish software-enforced properties from properties enforced by
secure hardware.

## Secure Core integration rule

Secure Core MUST NOT translate mere AVF presence into a trusted boundary.

The Android adapter must eventually provide, from genuine platform evidence:

1. a fresh verifier challenge binding;
2. authenticated VM identity / measurement;
3. a verified platform trust chain;
4. proof that the authorization service executes inside the pVM;
5. proof that monotonic security state used for rollback decisions is owned by
   that protected boundary;
6. a session key whose provenance is bound to that verified execution.

Until those are implemented and tested, the following remain false:

- platform attestation verified;
- monotonic hardware resistance established;
- hostile_host_ready;
- SCM-I10 adversarially tested.

## Separation from Android Keystore attestation

Key/ID attestation and VM remote attestation are different evidence domains.
Secure Core does not treat a hardware-backed Android Keystore certificate as
proof that the Secure Core authorization kernel itself is executing inside the
intended pVM.

## No synthetic roots

Test roots may exercise the generic certificate verifier, but they MUST NOT be
accepted as Android/AVF platform roots. Authoritative platform trust material
must be provisioned separately with pinned provenance and versioning.


## AOSP remote-attestation wire facts now implemented

The pVM payload requests attestation with `AVmPayload_requestAttestation(challenge)`.
AOSP documents an RKP-backed certificate chain and an attested private key known
only to the pVM. The leaf certificate carries extension OID
`1.3.6.1.4.1.11129.2.1.29.1`, containing the verifier challenge,
`isVmSecure`, and VM component name/securityVersion/codeHash/authorityHash.

Secure Core now parses that documented leaf extension strictly and verifies
challenge equality plus `isVmSecure=true`. This is still NOT sufficient for
PLATFORM_VERIFIED: the RKP-backed chain and authoritative trust policy must also
be validated, and expected component measurements/policy must be enforced.


## Component-policy gate

The verifier now enforces an explicit expected-component policy over the AOSP
attestation fields: exact component names (by default), minimum securityVersion,
pinned codeHash, and pinned authorityHash. A lower securityVersion is treated as
rollback and fails closed.

A generic caller-provided X.509 trust root can establish only
CRYPTOGRAPHICALLY_VERIFIED. PLATFORM_VERIFIED additionally requires the
separately provisioned authoritative Android AVF trust profile. No authoritative
root bundle is fabricated in this repository.


## Secretkeeper / rollback-protected persistence

AOSP documents Secretkeeper as a higher-privilege secure-storage service for
pVM clients. Its storage contract includes confidentiality, integrity,
persistence and rollback detection. Access is gated by DICE policy.

For updatable Microdroid VMs, AOSP documents a Secretkeeper-protected random
secret plus DICE sealing material. The pVM communicates with Secretkeeper over
an AuthGraph-derived encrypted channel even though Android transports the
messages and is treated as untrusted.

Secure Core therefore requires all of the following before mapping Secretkeeper
to a rollback-resistant monotonic security root:

- Secretkeeper identity verified by the pVM trust path;
- AuthGraph secure channel established;
- DICE policy-gated storage active;
- rollback-protected storage capability established.

The repository currently contains only the executable contract and a
fail-closed unavailable backend. No Android HAL/AuthGraph implementation is
claimed.
