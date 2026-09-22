"""Secret-free integrity receipts for authorization decisions."""

from __future__ import annotations
from collections.abc import Mapping
import hashlib
import json
from typing import Any


_FORBIDDEN_FIELDS = {"private_key", "secret", "seed", "key_bytes", "plaintext"}


def authorization_receipt(payload: Mapping[str, Any]) -> dict[str, Any]:
    lowered = {str(k).lower() for k in payload}
    leaked = sorted(lowered & _FORBIDDEN_FIELDS)
    if leaked:
        raise ValueError(f"secret-bearing receipt fields forbidden: {leaked}")
    body = dict(payload)
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return {"payload": body, "sha256": hashlib.sha256(canonical).hexdigest()}
