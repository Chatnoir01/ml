# Secure Core Mobile — AVF authoritative trust provisioning

Status: EXPERIMENTAL / NO PRODUCTION ANDROID ROOTS INCLUDED

## Goal

Prepare the exact trust-anchor profile that the authoritative AVF verifier is
allowed to use, without letting attacker-controlled runtime state choose both
the trust anchors and the expected profile pin.

This document describes two separate operations that MUST remain separate.

### 1. Offline preparation

Place reviewed DER-encoded CA certificates in a dedicated directory and run:

```bash
python scripts/prepare_secure_core_avf_trust.py \
  --anchors-dir /secure/offline/android-avf-anchors \
  --output avf-trust-candidate.json
```

The command:

- rejects symlinks;
- rejects non-DER entries;
- rejects malformed certificates;
- rejects non-CA certificates;
- rejects duplicate anchors;
- hashes each anchor with SHA-256;
- computes the canonical AVF profile SHA-256;
- writes a deterministic secret-free receipt.

The output has `authorization_status = candidate-pin-only`.

It is NOT trusted merely because the command succeeded.

### 2. Protected provisioning

The reviewed `profile_sha256` must be provisioned through a channel that is
outside attacker-controlled Android host state, for example immutable pVM image
configuration or another boundary with equivalent integrity guarantees.

The host/Python runtime deliberately has no authority to load this pin from an
environment variable, normal Android file, app preference, or GitHub artifact.

Secure Core now includes a native pVM-side loader in
`android_native/avf_profile_pin_bridge.cpp`. `Android.bp` exposes the
`secure_core_avf.profile_pin_hex` Soong value variable and injects
`SCM_AVF_PROFILE_PIN_HEX` only when that value is supplied. With no build-time
pin the native API returns `SCM_AVF_PROFILE_PIN_NOT_PROVISIONED`; malformed
values fail closed.

Example product configuration:

```make
SOONG_CONFIG_NAMESPACES += secure_core_avf
SOONG_CONFIG_secure_core_avf += profile_pin_hex
SOONG_CONFIG_secure_core_avf_profile_pin_hex := <reviewed-64-hex-profile-sha256>
```

The module is a `cc_library`, so Soong can provide both static and shared
variants. The shared variant is the ABI consumed by the Python native adapter;
loading that library still counts only as transport availability, not proof of
pVM execution.

Because this constant becomes part of the payload binary, changing it changes
the payload that AVF measures. This is the intended deployment direction, not a
claim that the current repository has already been measured on production
hardware. `ProtectedAvfProfilePinProviderUnavailable` remains the Python-side
fail-closed placeholder until the native payload integration owns the complete
runtime path.

## Runtime authorization path

The intended production chain is:

```text
reviewed Android/RKP anchor bundle
        |
        v
offline canonical profile SHA-256
        |
        v
protected deployment provisioning
        |
        v
PreprovisionedAvfProfilePin
        |
        v
AuthoritativeAvfTrustProfile
        |
        v
AndroidAvfAuthoritativeVerifier
        |
        v
PLATFORM_VERIFIED
        |
        v
pvmfw/Secretkeeper key binding
        |
        v
VerifiedSecretkeeperIdentity
        |
        v
AuthGraph session
```

A caller-controlled string, environment variable, normal Android app file,
ordinary GitHub artifact, or candidate receipt MUST NOT be treated as the
protected pin capability.

## Relationship to Android RKP

Android VM remote attestation relies on the RKP trust path and pVM DICE chain.
The RKP service checks device-rooted DICE identity and RKP VM markers before
provisioning VM-attestation credentials. Secure Core therefore does not ship a
synthetic production root bundle and does not infer Android authority from a
generic X.509 chain success.

Synthetic roots in unit tests only verify the software trust-transition logic.

## Current gate

The native pin loader and build-time Soong provisioning path now exist. The
remaining production gate is to provision real, reviewed Android/RKP trust
material and the reviewed profile pin into a measured pVM build, install that
build on supported hardware, then exercise the attestation + Secretkeeper +
AuthGraph chain against the real platform services.

Until then:

- `PLATFORM_VERIFIED` from synthetic tests is test evidence only;
- hostile-host resistance is not established;
- rollback-resistant Secretkeeper hardware state is not established;
- SCM-I10 remains below adversarially tested.
