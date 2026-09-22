"""Parser for Android AVF VM remote-attestation leaf extension.

OID and ASN.1 structure follow AOSP vm_remote_attestation.md. Parsing is strict
DER for the documented SEQUENCE/OCTET STRING/BOOLEAN/INTEGER/UTF8String subset.
This parser validates structure only; certificate-chain trust is separate.
"""

from __future__ import annotations
from dataclasses import dataclass

AVF_ATTESTATION_OID = "1.3.6.1.4.1.11129.2.1.29.1"


@dataclass(frozen=True)
class VmComponent:
    name: str
    security_version: int
    code_hash: bytes
    authority_hash: bytes


@dataclass(frozen=True)
class AvfAttestationExtension:
    attestation_challenge: bytes
    is_vm_secure: bool
    vm_components: tuple[VmComponent, ...]


def _length(data: bytes, pos: int) -> tuple[int, int]:
    if pos >= len(data):
        raise ValueError("truncated DER length")
    first = data[pos]; pos += 1
    if first < 0x80:
        return first, pos
    n = first & 0x7F
    if n == 0 or n > 4 or pos + n > len(data):
        raise ValueError("invalid DER length")
    raw = data[pos:pos+n]
    if raw[0] == 0:
        raise ValueError("non-minimal DER length")
    value = int.from_bytes(raw, "big")
    if value < 0x80:
        raise ValueError("non-minimal DER length")
    return value, pos + n


def _tlv(data: bytes, pos: int, tag: int) -> tuple[bytes, int]:
    if pos >= len(data) or data[pos] != tag:
        raise ValueError(f"unexpected DER tag at {pos}")
    size, start = _length(data, pos + 1)
    end = start + size
    if end > len(data):
        raise ValueError("truncated DER value")
    return data[start:end], end


def parse_avf_attestation_extension(der: bytes) -> AvfAttestationExtension:
    outer, end = _tlv(der, 0, 0x30)
    if end != len(der):
        raise ValueError("trailing DER data")
    challenge, p = _tlv(outer, 0, 0x04)
    boolean, p = _tlv(outer, p, 0x01)
    if boolean not in (b"\x00", b"\xff"):
        raise ValueError("non-canonical DER boolean")
    components_der, p = _tlv(outer, p, 0x30)
    if p != len(outer):
        raise ValueError("trailing attestation fields")

    components: list[VmComponent] = []
    q = 0
    while q < len(components_der):
        item, q = _tlv(components_der, q, 0x30)
        name_raw, x = _tlv(item, 0, 0x0C)
        version_raw, x = _tlv(item, x, 0x02)
        code_hash, x = _tlv(item, x, 0x04)
        authority_hash, x = _tlv(item, x, 0x04)
        if x != len(item) or not version_raw or (version_raw[0] & 0x80):
            raise ValueError("invalid VM component")
        if len(version_raw) > 1 and version_raw[0] == 0 and not (version_raw[1] & 0x80):
            raise ValueError("non-minimal DER integer")
        try:
            name = name_raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("invalid VM component name") from exc
        components.append(VmComponent(name, int.from_bytes(version_raw, "big"), code_hash, authority_hash))

    return AvfAttestationExtension(challenge, boolean == b"\xff", tuple(components))
