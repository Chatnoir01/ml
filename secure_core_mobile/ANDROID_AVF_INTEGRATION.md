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
