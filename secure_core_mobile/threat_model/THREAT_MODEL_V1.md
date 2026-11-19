# Secure Core Mobile — Threat Model v1

Status: FROZEN BASELINE / EXPERIMENTAL

## Protected assets

- private/signing/decryption key material;
- authorization policy and policy version;
- key lifecycle state;
- freshness counters/nonces;
- attestation evidence;
- authorization transcripts and integrity receipts.

## Primary adversary

The main Android application/host environment may be compromised. The adversary
may invoke exposed APIs, reorder/replay requests, modify ordinary app storage,
kill/restart processes, supply malformed input, and attempt rollback to older
host-visible state.

## Initially out of scope

Until separately tested, v1 does not claim resistance to:
- physical invasive hardware attacks;
- compromised secure-element/StrongBox firmware;
- broken cryptographic primitives;
- malicious silicon/vendor root of trust;
- side channels not explicitly measured;
- coercion or compromised user intent;
- availability/DoS by a fully compromised host.

## Central forbidden condition

For every operation classified by policy as forbidden in the current trusted
authorization state, control of the ordinary host alone must not be sufficient
to obtain the corresponding protected cryptographic operation.

This is a HYPOTHESIS, not a demonstrated property.

## Core invariants

SCM-I1 — deny by default:
Unknown operation, policy, capability, state, or evidence => DENY.

SCM-I2 — no raw-secret authorization:
Application-facing authorization uses opaque key handles, not exported private
key bytes.

SCM-I3 — policy before crypto:
A provider operation cannot be reached before a successful policy/state
authorization decision for that exact request.

SCM-I4 — request binding:
Authorization evidence binds operation, key handle, policy version, state,
freshness material and relevant caller/context identity.

SCM-I5 — replay rejection:
Evidence already consumed, expired, stale or outside its freshness window cannot
authorize a new protected operation.

SCM-I6 — rollback visibility:
Security-relevant state rollback must either be prevented by the stronger
boundary or detected and denied. Host storage alone is not trusted evidence of
freshness.

SCM-I7 — capability honesty:
SIMULATED/software fallback cannot satisfy a HARDWARE_BACKED requirement.

SCM-I8 — receipt secrecy:
Receipts may prove decisions/integrity but contain no secret key material.

SCM-I9 — claim honesty:
Implementation/test status cannot silently promote a security claim.

SCM-I10 — hostile-host evidence:
Only experiments actually executed with the declared hostile-host boundary can
promote the central claim toward ADVERSARIALLY_TESTED.

## Required negative tests

- unknown operation;
- unknown key handle;
- revoked/destroyed key;
- malformed policy;
- policy-version mismatch;
- stale nonce;
- repeated nonce;
- counter rollback;
- altered request after authorization;
- software fallback when hardware required;
- missing/invalid attestation;
- host restart between authorization steps;
- duplicated authorization transcript.

Each negative test must produce an auditable denial without secret leakage.
