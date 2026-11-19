"""Secret-free deterministic integrity receipts."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
import hashlib
import json
import re
from typing import Any


_FORBIDDEN_EXACT = {
    "private_key", "privatekey", "secret", "seed", "key_bytes", "keybytes",
    "plaintext", "password", "passphrase", "recovery_phrase", "mnemonic",
}
_FORBIDDEN_PATTERN = re.compile(
    r"(private.?key|secret|seed|key.?bytes|plaintext|password|passphrase|mnemonic)",
    re.IGNORECASE,
)


def _scan(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_EXACT or _FORBIDDEN_PATTERN.search(normalized):
                raise ValueError(f"secret-bearing receipt field forbidden at {path}.{key}")
            _scan(child, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan(child, f"{path}[{index}]")
        return
    if isinstance(value, (bytes, bytearray)):
        raise ValueError(f"raw bytes forbidden in receipt at {path}")


def authorization_receipt(payload: Mapping[str, Any]) -> dict[str, Any]:
    _scan(payload)
    body = dict(payload)
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode()
    return {"payload": body, "sha256": hashlib.sha256(canonical).hexdigest()}
