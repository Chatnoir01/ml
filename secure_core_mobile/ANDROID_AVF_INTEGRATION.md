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


## AuthGraph + SecretManagement protocol contract

AOSP SecretManagement.cddl fixes the core request opcodes to GetVersion=1,
StoreSecret=2 and GetSecret=3. SecretId is exactly 64 bytes and Secret is
exactly 32 bytes. StoreSecret requires a CBOR-encoded DICE sealing policy.

The pVM client is AuthGraph P1/source and Secretkeeper is P2/sink. Secretkeeper's
identity is a per-boot public key. For Microdroid, AOSP transports that
CBOR-encoded COSE public key through the protected AVF device-tree path at
/proc/device-tree/avf/secretkeeper_public_key; pvmfw verifies it against the VM
reference DT before the guest consumes it.

Secure Core now models these protocol sizes and the fail-closed session
transition. The protected device-tree Secretkeeper-key retrieval path is now
implemented as a bounded, exact-path, fail-closed input boundary. Reading that
property does not verify Secretkeeper identity and cannot establish platform
trust. Native AuthGraph key exchange, authoritative Secretkeeper identity
verification, and Binder/HAL transport remain unimplemented.


## COSE_Encrypt0 development codec

Secure Core now has an executable AES-256-GCM Encrypt0 development codec with
authentication bound to the AuthGraph session identifier and request sequence
number. Negative tests cover ciphertext mutation, IV mutation, session
substitution and sequence substitution.

The codec intentionally supports only a narrow canonical-CBOR subset and is
labelled development-only. It MUST NOT be treated as AOSP wire compatibility
until tested byte-for-byte against authoritative Secretkeeper/AuthGraph vectors
or a real Android implementation.


## AOSP source reconciliation

A source audit found two SecretManagement CDDL generations. The current AOSP
file defines COSE Encrypt0 AAD with empty external_aad. An older/release branch
explicitly binds RequestSeqNum as external AAD. Secure Core therefore no longer
silently assumes one wire generation: the codec has an explicit ExternalAadMode
and defaults to the current-AOSP EMPTY mode. Sequence-AAD compatibility is
retained only as an explicit legacy/versioned mode.

The AOSP VTS client confirms the architectural split of two AuthGraph AES keys:
aes_keys[0] protects client->Secretkeeper requests and aes_keys[1] protects
Secretkeeper->client responses, with the AuthGraph session_id supplied to the
COSE cipher layer.


## AOSP SkSession reconciliation

Current AOSP Secretkeeper client code maintains two independent AES keys
(encryption_key and decryption_key), one AuthGraph session_id, and independent
outgoing/incoming SeqNum counters. The outgoing sequence is consumed for request
AAD and the incoming sequence for response AAD.

Secure Core now mirrors that state split in SecretkeeperSessionCore. Failed
response authentication does not consume the incoming sequence. A response
encrypted with the request-direction key is rejected.

This remains transport-independent: Binder ISecretkeeper and native AuthGraph
key exchange are not simulated as trusted platform behavior.


## DICE policy semantics implemented

Secure Core now models the AOSP DICE policy v1 constraint semantics used by
Secretkeeper: ExactMatch (type 1), GreaterOrEqual (type 2), exact chain-length
matching, and explicit missing-value behavior.

The Microdroid profile models AOSP's update-safe sealing rule: AUTHORITY_HASH
and MODE are exact matches while SECURITY_VERSION is GreaterOrEqual. Payload
subcomponents likewise pin authority and permit only non-decreasing security
versions. This is an executable semantic model, not yet the authoritative CBOR
wire encoder/path-label implementation.


## Android DICE numeric paths + wire encoder

AOSP VTS pins Android DICE labels used by Secretkeeper sealing policy:
AUTHORITY_HASH=-4670549, CONFIG_DESC=-4670548, KEY_MODE=-4670551,
COMPONENT_NAME=-70002, COMPONENT_VERSION=-70003, SECURITY_VERSION=-70005.

Secure Core now pins those constants and emits a deterministic CBOR subset for
DicePolicy v1 using numeric paths. This removes the previous symbolic-path gap.
It is still not called byte-for-byte AOSP compatible until golden vectors from
AOSP's Rust policy builder are imported and compared.


## DICE policy builder behavior

The AOSP builder constructs policy from the observed DICE chain. It exact-matches
the first two chain nodes (version and root public key), then applies requested
ConstraintSpecs to later certificate nodes. MissingAction::Ignore skips a
constraint only while policy is being built; it does not weaken later matching.

Secure Core now has the same builder semantics over an already-decoded chain
model, including fail/ignore handling and integer enforcement for
GreaterOrEqual. DICE certificate-chain CBOR decoding is still outside this
module and remains a separate compatibility gate.


## First byte-for-byte AOSP golden vector

AOSP libsecretkeeper_client contains a deterministic ExplicitKeyDiceCertChain
unit vector. Its unordered root COSE_Key {"a":1, 3:-7, 1234:1, 1:1} must
canonicalize to a4010103261904d201616101 and the complete two-node explicit
chain must be 82014ca4010103261904d201616101.

Secure Core now reproduces that authoritative vector byte-for-byte and tests
that input map order cannot alter the resulting explicit chain. This validates
the minimal root-key canonicalization path only; COSE_Sign1 DiceChainEntry
decoding/signature verification remains a separate gate.


## COSE_Sign1 DICE entry structural parsing

AOSP dice_policy treats explicit-chain nodes 0 and 1 directly, then parses each
later DiceChainEntry as COSE_Sign1 and decodes the embedded payload as CBOR
before applying policy constraints. Secure Core now implements that structural
path with strict truncation, canonical integer/length, duplicate-map-key and
trailing-data rejection.

Successful payload extraction is explicitly NOT signature verification. The
next gate must verify each COSE_Sign1 signature and public-key chaining before
any parsed chain can contribute authenticity evidence.


## COSE_Sign1 cryptographic verification gate

Secure Core now verifies the COSE Sig_structure
["Signature1", protected, external_aad, payload] for an ES256/P-256 subset.
COSE's raw 64-byte R||S signature is converted to the DER representation
expected by the cryptography backend. Tests reject payload mutation, a wrong
parent key and an unexpected protected algorithm.

This proves only signature validity under the supplied parent key. Full DICE
chain verification still requires extracting each next subject public key from
the authenticated DICE payload and carrying it forward as the next parent.
Platform provenance remains a separate gate.


## Multi-hop DICE signature chaining

Secure Core now verifies a multi-hop ES256 DICE subset. After each COSE_Sign1
signature succeeds, SUBJECT_PUBLIC_KEY is read only from that authenticated
payload, decoded as an EC2/P-256/ES256 COSE_Key, and carried forward as the
parent verifier for the next entry. Tests include a two-hop root->middle->leaf
chain and reject a second certificate signed by an unrelated attacker key.

This establishes cryptographic chain continuity under the caller-supplied root.
It still does not establish that the root itself is Android/AVF authoritative,
and therefore cannot independently produce PLATFORM_VERIFIED evidence.


## AuthGraph peer_identity binding

AOSP Secretkeeper uses peer_identity returned by the AuthGraph exchange as the
client DICE chain supplied to policy-gated storage. Secure Core now models that
binding explicitly: a policy authorization context is tied to both the
AuthGraph session_id and a digest of the exact peer_identity DICE chain.

Tests reject substitution of an attacker-provided chain and replay of a valid
peer identity into another session. This closes the semantic gap where a
cryptographically valid but unrelated DICE chain could otherwise be passed to
policy evaluation.

This is still an integration contract. Until the native AuthGraph exchange
produces the peer_identity in-process, test-created AuthGraphPeerIdentity values
must not be treated as platform evidence.
