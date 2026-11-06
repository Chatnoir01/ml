"""Read-only Phase 2R checkpoint-zero observation helpers.

Engineering-only instrumentation. Never launches training, reconstructs a historical
Phase 2G state, changes a frozen result or authorizes Phase 2U/2I.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .phase2g_shared_model import _serialize_model_state

_NAMES = ("w1", "b1", "w2", "b2", "w3", "b3")


def _canonical_json(value: Any) -> bytes:
    """Encode NumPy RNG state without drawing from the generator."""
    import numpy as np

    def encode(obj: Any) -> Any:
        if isinstance(obj, Mapping):
            return {str(k): encode(v) for k, v in obj.items()}
        if isinstance(obj, (tuple, list)):
            return [encode(v) for v in obj]
        if isinstance(obj, np.ndarray):
            return {"dtype": obj.dtype.str, "shape": list(obj.shape),
                    "values": encode(obj.tolist())}
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        raise TypeError("unsupported RNG state value")

    return json.dumps(encode(value), sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def observe_checkpoint_zero(*, tensors: Mapping[str, Any], rng: Any) -> dict[str, Any]:
    """Hash exact initialized float32 tensors and RNG state, without mutation.

    Call AFTER initialization but BEFORE epoch shuffling/optimizer updates.
    This does not record optimizer state, dataset hashes or final weights.
    The existing Phase-2G serializer is reused exactly; no new wire encoding.
    """
    import numpy as np

    if not isinstance(tensors, Mapping) or set(tensors) != set(_NAMES):
        raise ValueError("expected exactly six initialized model tensors")
    if not isinstance(rng, np.random.Generator):
        raise ValueError("expected numpy.random.Generator")
    checked: dict[str, Any] = {}
    for name in _NAMES:
        array = np.asarray(tensors[name])
        if array.dtype != np.dtype("float32"):
            raise ValueError(f"{name} must be float32 without implicit conversion")
        if not np.isfinite(array).all():
            raise ValueError(f"{name} contains non-finite values")
        checked[name] = array
    before = _canonical_json(rng.bit_generator.state)
    model_bytes = _serialize_model_state(**checked)
    after = _canonical_json(rng.bit_generator.state)
    if before != after:
        raise RuntimeError("observation mutated NumPy RNG state")
    return {
        "schema_version": 1,
        "scope": "phase2r_checkpoint0_instrumentation_only",
        "initialization_sha256": hashlib.sha256(model_bytes).hexdigest(),
        "rng_state_sha256": hashlib.sha256(before).hexdigest(),
        "numpy_version": np.__version__,
        "tensor_shapes": {name: list(checked[name].shape) for name in _NAMES},
        "neural_training_performed": False,
        "historical_phase2g_anomaly_explained": False,
    }
