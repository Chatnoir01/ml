"""Fail-closed retrieval of the pvmfw-sanitized Secretkeeper public key.

Reading the protected AVF device-tree property is a transport/input step only.
It does not verify Secretkeeper identity and cannot by itself establish
platform trust.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .authgraph_session import PvmfwValidatedSecretkeeperKey
from .secretkeeper_cose_key import parse_secretkeeper_cose_key

TRUSTED_SECRETKEEPER_DT_PATH = Path(
    "/proc/device-tree/avf/secretkeeper_public_key"
)
MAX_SECRETKEEPER_KEY_BYTES = 64 * 1024


def _read_bounded(path: Path) -> bytes:
    with path.open("rb") as handle:
        data = handle.read(MAX_SECRETKEEPER_KEY_BYTES + 1)
    return data


def read_pvmfw_secretkeeper_key(
    *,
    path: Path | str = TRUSTED_SECRETKEEPER_DT_PATH,
    reader: Callable[[Path], bytes] = _read_bounded,
) -> PvmfwValidatedSecretkeeperKey:
    """Read only the trusted AVF DT property and preserve its provenance.

    The injectable reader exists for deterministic tests. The path remains
    fixed by policy and is validated before the reader is invoked.
    """

    candidate = Path(path)
    if candidate != TRUSTED_SECRETKEEPER_DT_PATH:
        raise ValueError("Secretkeeper key must come from trusted /avf DT path")

    try:
        raw = reader(candidate)
    except OSError as exc:
        raise RuntimeError("Secretkeeper AVF device-tree key unavailable") from exc

    if not isinstance(raw, (bytes, bytearray)):
        raise TypeError("Secretkeeper AVF device-tree reader must return bytes")

    key = bytes(raw)
    if not key:
        raise ValueError("empty Secretkeeper public key")
    if len(key) > MAX_SECRETKEEPER_KEY_BYTES:
        raise ValueError("Secretkeeper public key exceeds bounded input size")

    # The trusted path is necessary provenance, but malformed or unsupported
    # COSE keys must still fail closed before they enter AuthGraph state.
    parse_secretkeeper_cose_key(key)

    return PvmfwValidatedSecretkeeperKey(
        public_key_cbor=key,
        source_path=str(TRUSTED_SECRETKEEPER_DT_PATH),
    )
