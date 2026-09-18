"""Held-out-blind terminal freeze for preregistered Phase 2G.

This module performs no neural training, candidate scoring, evolution, or held-out
H evaluation. It accepts only already-completed arm-cell records, validates the
full preregistered pre-H provenance, and emits a deterministic 36-cell manifest.
Held-out H may be authorized only from an intact manifest produced here.

No held-out dataset/model seed constant is imported or consumed by this module.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from typing import Any

from .cryptoshield import validate_sbox
from .phase2g import (
    ARMS,
    CHECKPOINT_GENERATIONS,
    CHECKPOINT_TRAININGS_PER_CELL,
    EVOLUTION_SEEDS,
    SCORING_DATASET_BASE_SEEDS,
    TRAINING_DATASET_BASE_SEEDS,
    TRAINING_MODEL_BASE_SEEDS,
    TRAININGS_PER_CHECKPOINT,
    expanded_checkpoint_seed_block,
)
from .provenance import fingerprint_sbox

CLASSICAL_EVALUATIONS_PER_CELL = 340
TERMINAL_SELECTION_RULE = "historical_classical_only"
CELL_COUNT = len(ARMS) * len(EVOLUTION_SEEDS)
POPULATION_SIZE = 20
SHORTLIST_SIZE = 8
PARENT_COUNT = 4
PROPOSALS_PER_GENERATION = 16
GENERATION_COUNT = 20
CLASSICAL_LEDGER_FIELDS = (
    "fingerprint",
    "nonlinearity",
    "differential_uniformity",
    "max_abs_lat",
    "sac_score",
    "algebraic_degree",
)
TERMINAL_CLASSICAL_FIELDS = (
    "admissible",
    "nonlinearity",
    "differential_uniformity",
    "max_abs_lat",
    "algebraic_degree",
)


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _is_hex64(value: object) -> bool:
    text = str(value)
    if len(text) != 64:
        return False
    try:
        int(text, 16)
    except ValueError:
        return False
    return True


def _expected_cells() -> set[tuple[int, str]]:
    return {(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in ARMS}


def _sequence(raw: object, *, role: str, length: int | None = None) -> list[Any]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise ValueError(f"Phase-2G provenance {role} must be a sequence")
    frozen = list(raw)
    if length is not None and len(frozen) != length:
        raise ValueError(
            f"Phase-2G provenance {role} must contain exactly {length} entries"
        )
    return frozen


def _fingerprints(
    raw: object,
    *,
    role: str,
    length: int | None = None,
    unique: bool = True,
) -> list[str]:
    values = [str(value) for value in _sequence(raw, role=role, length=length)]
    if not all(_is_hex64(value) for value in values):
        raise ValueError(f"Phase-2G provenance {role} contains invalid fingerprints")
    if unique and len(set(values)) != len(values):
        raise ValueError(f"Phase-2G provenance {role} contains duplicate fingerprints")
    return values


def _population_digest(fingerprints: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(fingerprints).encode("ascii")).hexdigest()


def _freeze_terminal_classical(raw: object) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError("Phase-2G terminal classical metrics are missing")
    missing = [field for field in TERMINAL_CLASSICAL_FIELDS if field not in raw]
    if missing:
        raise ValueError(f"Phase-2G terminal classical metrics missing {missing!r}")
    if not isinstance(raw["admissible"], bool):
        raise ValueError("Phase-2G terminal admissibility must be boolean")
    return {
        "admissible": bool(raw["admissible"]),
        "nonlinearity": int(raw["nonlinearity"]),
        "differential_uniformity": int(raw["differential_uniformity"]),
        "max_abs_lat": int(raw["max_abs_lat"]),
        "algebraic_degree": int(raw["algebraic_degree"]),
    }


def _verify_scientific_payload_receipt(raw: Mapping[str, Any]) -> str:
    stored = str(raw.get("scientific_payload_sha256", ""))
    if not _is_hex64(stored):
        raise ValueError("Phase-2G scientific payload receipt is missing or invalid")
    clean = {key: value for key, value in raw.items() if key != "scientific_payload_sha256"}
    if _sha256(clean) != stored:
        raise ValueError("Phase-2G scientific payload receipt mismatch")
    return stored


def _validate_generation_trace(
    raw: object,
    *,
    initial_digest: str,
    terminal_population_digest: str,
    terminal_fingerprint: str,
) -> tuple[list[dict[str, Any]], set[str], dict[str, set[str]], list[str]]:
    rows = _sequence(raw, role="generation trace", length=GENERATION_COUNT)
    normalized: list[dict[str, Any]] = []
    evaluated: set[str] = set()
    proposal_parents: dict[str, set[str]] = {}
    initial_fingerprints: list[str] | None = None
    previous_next: list[str] | None = None

    for expected_generation, item in enumerate(rows):
        if not isinstance(item, Mapping):
            raise ValueError("Phase-2G provenance generation trace row must be a mapping")
        generation = int(item.get("generation", -1))
        if generation != expected_generation:
            raise ValueError("Phase-2G provenance generation trace order drift")

        population_before = _fingerprints(
            item.get("population_before"),
            role=f"generation {generation} population_before",
            length=POPULATION_SIZE,
        )
        shortlist = _fingerprints(
            item.get("shortlist"),
            role=f"generation {generation} shortlist",
            length=SHORTLIST_SIZE,
        )
        parents = _fingerprints(
            item.get("parents"),
            role=f"generation {generation} parents",
            length=PARENT_COUNT,
        )
        proposals = _fingerprints(
            item.get("proposals"),
            role=f"generation {generation} proposals",
            length=PROPOSALS_PER_GENERATION,
        )
        next_population = _fingerprints(
            item.get("next_population"),
            role=f"generation {generation} next_population",
            length=POPULATION_SIZE,
        )

        if previous_next is not None and population_before != previous_next:
            raise ValueError("Phase-2G provenance generation population continuity drift")
        if not set(shortlist).issubset(population_before):
            raise ValueError("Phase-2G provenance shortlist contains non-population candidate")
        if not set(parents).issubset(shortlist):
            raise ValueError("Phase-2G provenance parent contains non-shortlisted candidate")
        if set(proposals) & evaluated:
            raise ValueError("Phase-2G provenance proposal reuses an earlier evaluated candidate")
        if not set(next_population).issubset(set(population_before) | set(proposals)):
            raise ValueError("Phase-2G provenance survival population contains unknown candidate")

        if initial_fingerprints is None:
            initial_fingerprints = population_before
            evaluated.update(population_before)
        evaluated.update(proposals)
        parent_set = set(parents)
        for proposal in proposals:
            proposal_parents[proposal] = parent_set

        normalized.append(
            {
                "generation": generation,
                "population_before": population_before,
                "shortlist": shortlist,
                "parents": parents,
                "proposals": proposals,
                "next_population": next_population,
            }
        )
        previous_next = next_population

    if initial_fingerprints is None or previous_next is None:
        raise ValueError("Phase-2G provenance generation trace is empty")
    if _population_digest(initial_fingerprints) != initial_digest:
        raise ValueError("Phase-2G provenance initial population digest mismatch")
    if _population_digest(previous_next) != terminal_population_digest:
        raise ValueError("Phase-2G provenance terminal population digest mismatch")
    if terminal_fingerprint not in previous_next:
        raise ValueError("Phase-2G provenance terminal is absent from final population")
    if len(evaluated) != CLASSICAL_EVALUATIONS_PER_CELL:
        raise ValueError("Phase-2G provenance trace must contain exactly 340 unique evaluations")
    return normalized, evaluated, proposal_parents, initial_fingerprints


def _validate_classical_ledger(
    raw: object,
    *,
    evaluated: set[str],
    terminal_fingerprint: str,
    terminal_classical: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = _sequence(raw, role="classical evaluation ledger", length=CLASSICAL_EVALUATIONS_PER_CELL)
    normalized: list[dict[str, Any]] = []
    fingerprints_seen: set[str] = set()
    terminal_row: dict[str, Any] | None = None
    for item in rows:
        if not isinstance(item, Mapping):
            raise ValueError("Phase-2G provenance classical ledger row must be a mapping")
        if set(item) != set(CLASSICAL_LEDGER_FIELDS):
            raise ValueError("Phase-2G provenance classical ledger field drift")
        fingerprint = str(item["fingerprint"])
        if not _is_hex64(fingerprint) or fingerprint in fingerprints_seen:
            raise ValueError("Phase-2G provenance classical ledger fingerprint drift")
        row = {
            "fingerprint": fingerprint,
            "nonlinearity": int(item["nonlinearity"]),
            "differential_uniformity": int(item["differential_uniformity"]),
            "max_abs_lat": int(item["max_abs_lat"]),
            "sac_score": float(item["sac_score"]),
            "algebraic_degree": int(item["algebraic_degree"]),
        }
        fingerprints_seen.add(fingerprint)
        normalized.append(row)
        if fingerprint == terminal_fingerprint:
            terminal_row = row
    if fingerprints_seen != evaluated:
        raise ValueError("Phase-2G provenance classical ledger does not match generation trace")
    if terminal_row is None:
        raise ValueError("Phase-2G provenance terminal is absent from classical ledger")
    for field in (
        "nonlinearity",
        "differential_uniformity",
        "max_abs_lat",
        "algebraic_degree",
    ):
        if int(terminal_row[field]) != int(terminal_classical[field]):
            raise ValueError("Phase-2G provenance terminal classical metrics mismatch")
    return normalized


def _validate_parent_map(
    raw: object,
    *,
    proposal_parents: Mapping[str, set[str]],
) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        raise ValueError("Phase-2G provenance parent_map must be a mapping")
    normalized = {str(child): str(parent) for child, parent in raw.items()}
    if set(normalized) != set(proposal_parents):
        raise ValueError("Phase-2G provenance parent_map must cover all 320 proposals")
    for child, parent in normalized.items():
        if not _is_hex64(child) or not _is_hex64(parent):
            raise ValueError("Phase-2G provenance parent_map fingerprint drift")
        if parent not in proposal_parents[child]:
            raise ValueError("Phase-2G provenance proposal parent is not a selected parent")
    return dict(sorted(normalized.items()))


def _validate_model_receipts(
    raw: object,
    *,
    t_seeds: Sequence[int],
    m_seeds: Sequence[int],
) -> list[dict[str, Any]]:
    rows = _sequence(raw, role="checkpoint model receipts", length=TRAININGS_PER_CHECKPOINT)
    normalized: list[dict[str, Any]] = []
    identities: set[tuple[int, int]] = set()
    for item in rows:
        if not isinstance(item, Mapping):
            raise ValueError("Phase-2G provenance model receipt must be a mapping")
        difference = int(item.get("difference", -1))
        replicate = int(item.get("replicate", -1))
        identity = (difference, replicate)
        if difference not in (0x00000001, 0x00000100) or replicate not in range(8):
            raise ValueError("Phase-2G provenance model receipt identity drift")
        if identity in identities:
            raise ValueError("Phase-2G provenance duplicate model receipt identity")
        identities.add(identity)
        if int(item.get("dataset_seed", -1)) != int(t_seeds[replicate]):
            raise ValueError("Phase-2G provenance checkpoint T seed/model receipt mismatch")
        if int(item.get("model_seed", -1)) != int(m_seeds[replicate]):
            raise ValueError("Phase-2G provenance checkpoint M seed/model receipt mismatch")
        state_sha = str(item.get("state_sha256", ""))
        if not _is_hex64(state_sha):
            raise ValueError("Phase-2G provenance checkpoint model state receipt invalid")
        normalized.append(
            {
                "difference": difference,
                "replicate": replicate,
                "dataset_seed": int(t_seeds[replicate]),
                "model_seed": int(m_seeds[replicate]),
                "state_sha256": state_sha,
            }
        )
    expected = {(difference, replicate) for difference in (1, 256) for replicate in range(8)}
    if identities != expected:
        raise ValueError("Phase-2G provenance checkpoint model grid incomplete")
    return sorted(normalized, key=lambda row: (row["difference"], row["replicate"]))


def _validate_score_receipts(
    raw: object,
    *,
    arm: str,
    seed: int,
    generation: int,
    q_seeds: Sequence[int],
    cache_misses: int,
    evaluated: set[str],
) -> list[dict[str, Any]]:
    rows = _sequence(raw, role="checkpoint score receipts")
    if len(rows) != cache_misses:
        raise ValueError("Phase-2G provenance score cache miss/receipt count mismatch")
    normalized: list[dict[str, Any]] = []
    cache_keys: set[tuple[str, int, int, str]] = set()
    for item in rows:
        if not isinstance(item, Mapping):
            raise ValueError("Phase-2G provenance score receipt must be a mapping")
        fingerprint = str(item.get("fingerprint", ""))
        if not _is_hex64(fingerprint) or fingerprint not in evaluated:
            raise ValueError("Phase-2G provenance score receipt candidate drift")
        cache_key_raw = _sequence(item.get("cache_key"), role="score cache key", length=4)
        cache_key = (
            str(cache_key_raw[0]),
            int(cache_key_raw[1]),
            int(cache_key_raw[2]),
            str(cache_key_raw[3]),
        )
        if cache_key != (arm, seed, generation, fingerprint) or cache_key in cache_keys:
            raise ValueError("Phase-2G provenance score cache key drift")
        cache_keys.add(cache_key)
        if int(item.get("training_count", -1)) != 0:
            raise ValueError("Phase-2G provenance candidate scoring must remain inference-only")
        payload_sha = str(item.get("payload_sha256", ""))
        if not _is_hex64(payload_sha):
            raise ValueError("Phase-2G provenance score payload receipt invalid")
        payload = item.get("payload")
        if not isinstance(payload, Mapping):
            raise ValueError("Phase-2G provenance score payload must be a mapping")
        stored_payload_sha = str(payload.get("scientific_payload_sha256", ""))
        if stored_payload_sha != payload_sha:
            raise ValueError("Phase-2G provenance score payload linkage failure")
        clean_payload = {
            key: value for key, value in payload.items() if key != "scientific_payload_sha256"
        }
        if _sha256(clean_payload) != payload_sha:
            raise ValueError("Phase-2G provenance score payload integrity failure")
        if int(payload.get("training_count", -1)) != 0:
            raise ValueError("Phase-2G provenance score payload training-count drift")
        payload_fingerprint = str(
            payload.get("candidate_fingerprint", payload.get("fingerprint", ""))
        )
        if payload_fingerprint != fingerprint:
            raise ValueError("Phase-2G provenance score payload fingerprint drift")
        per_model = payload.get("models")
        if per_model is not None:
            model_rows = _sequence(per_model, role="candidate inference model receipts", length=16)
            observed_q: dict[int, int] = {}
            for model_row in model_rows:
                if not isinstance(model_row, Mapping):
                    raise ValueError("Phase-2G provenance inference model receipt malformed")
                replicate = int(model_row.get("replicate", -1))
                if replicate not in range(8):
                    raise ValueError("Phase-2G provenance inference replicate drift")
                q_seed = int(model_row.get("scoring_dataset_seed", -1))
                if q_seed != int(q_seeds[replicate]):
                    raise ValueError("Phase-2G provenance Q seed/inference receipt mismatch")
                observed_q[replicate] = q_seed
            if set(observed_q) != set(range(8)):
                raise ValueError("Phase-2G provenance Q seed receipt grid incomplete")
        normalized.append(
            {
                "cache_key": list(cache_key),
                "fingerprint": fingerprint,
                "neural_advantage": float(item.get("neural_advantage", 0.0)),
                "payload_sha256": payload_sha,
                "training_count": 0,
            }
        )
    return sorted(normalized, key=lambda row: tuple(row["cache_key"]))


def _freeze_checkpoints(
    raw: object,
    *,
    arm: str,
    seed: int,
    generation_trace: Sequence[Mapping[str, Any]],
    initial_fingerprints: Sequence[str],
    evaluated: set[str],
) -> list[dict[str, Any]]:
    rows = _sequence(raw, role="checkpoints", length=len(CHECKPOINT_GENERATIONS))
    indexed: dict[int, dict[str, Any]] = {}
    for item in rows:
        if not isinstance(item, Mapping):
            raise ValueError("Phase-2G provenance checkpoint receipt must be a mapping")
        generation = int(item.get("generation", -1))
        if generation not in CHECKPOINT_GENERATIONS or generation in indexed:
            raise ValueError("Phase-2G provenance invalid or duplicate checkpoint generation")
        checkpoint_index = CHECKPOINT_GENERATIONS.index(generation)
        if int(item.get("checkpoint_generation", -1)) != generation:
            raise ValueError("Phase-2G provenance checkpoint generation identity drift")
        if int(item.get("block_start_generation", -1)) != generation:
            raise ValueError("Phase-2G provenance checkpoint block start drift")
        if int(item.get("block_end_generation", -1)) != generation + 5:
            raise ValueError("Phase-2G provenance checkpoint block end drift")
        if bool(item.get("selection_enabled", False)) != (arm != "C"):
            raise ValueError("Phase-2G provenance checkpoint selection flag drift")
        if int(item.get("training_count", -1)) != TRAININGS_PER_CHECKPOINT:
            raise ValueError("Phase-2G provenance checkpoint training-count drift")
        if int(item.get("classical_evaluations", -1)) != 80:
            raise ValueError("Phase-2G provenance checkpoint classical-budget drift")
        training_receipt = str(item.get("training_receipt_sha256", ""))
        if not _is_hex64(training_receipt):
            raise ValueError("Phase-2G provenance checkpoint training receipt invalid")

        population_before = _fingerprints(
            item.get("population_before_fingerprints"),
            role=f"checkpoint {generation} population_before",
            length=POPULATION_SIZE,
        )
        expected_before = list(generation_trace[generation]["population_before"])
        if population_before != expected_before:
            raise ValueError("Phase-2G provenance checkpoint population-before linkage drift")
        population_after = _fingerprints(
            item.get("population_after_fingerprints"),
            role=f"checkpoint {generation} population_after",
            length=POPULATION_SIZE,
        )
        expected_after = list(generation_trace[generation + 4]["next_population"])
        if population_after != expected_after:
            raise ValueError("Phase-2G provenance checkpoint population-after linkage drift")

        curriculum = _fingerprints(
            item.get("curriculum_fingerprints"),
            role=f"checkpoint {generation} curriculum",
            length=POPULATION_SIZE,
        )
        expected_curriculum = list(initial_fingerprints) if arm == "F" else expected_before
        if set(curriculum) != set(expected_curriculum):
            raise ValueError("Phase-2G provenance checkpoint curriculum identity drift")
        curriculum_digest = str(item.get("curriculum_digest_sha256", ""))
        if not _is_hex64(curriculum_digest) or _population_digest(curriculum) != curriculum_digest:
            raise ValueError("Phase-2G provenance checkpoint curriculum digest mismatch")

        expected_t = list(
            expanded_checkpoint_seed_block(TRAINING_DATASET_BASE_SEEDS, checkpoint_index)
        )
        expected_m = list(
            expanded_checkpoint_seed_block(TRAINING_MODEL_BASE_SEEDS, checkpoint_index)
        )
        expected_q = list(
            expanded_checkpoint_seed_block(SCORING_DATASET_BASE_SEEDS, checkpoint_index)
        )
        t_seeds = [
            int(value)
            for value in _sequence(
                item.get("training_dataset_seeds"), role="checkpoint T seeds", length=8
            )
        ]
        m_seeds = [
            int(value)
            for value in _sequence(
                item.get("training_model_seeds"), role="checkpoint M seeds", length=8
            )
        ]
        q_seeds = [
            int(value)
            for value in _sequence(
                item.get("scoring_dataset_seeds"), role="checkpoint Q seeds", length=8
            )
        ]
        if t_seeds != expected_t or m_seeds != expected_m or q_seeds != expected_q:
            raise ValueError("Phase-2G provenance checkpoint T/M/Q seed drift")

        model_receipts = _validate_model_receipts(
            item.get("model_receipts"), t_seeds=t_seeds, m_seeds=m_seeds
        )
        cache_hits = int(item.get("score_cache_hits", -1))
        cache_misses = int(item.get("score_cache_misses", -1))
        if cache_hits < 0 or cache_misses < 0:
            raise ValueError("Phase-2G provenance score cache counts must be non-negative")
        score_receipts = _validate_score_receipts(
            item.get("score_receipts"),
            arm=arm,
            seed=seed,
            generation=generation,
            q_seeds=q_seeds,
            cache_misses=cache_misses,
            evaluated=evaluated,
        )
        shuffle_seed = item.get("shuffle_rng_seed")
        if arm == "S":
            if shuffle_seed is None:
                raise ValueError("Phase-2G provenance S checkpoint shuffle seed missing")
            shuffle_seed = int(shuffle_seed)
        elif shuffle_seed is not None:
            raise ValueError("Phase-2G provenance non-S checkpoint has shuffle seed")

        indexed[generation] = {
            "generation": generation,
            "training_count": TRAININGS_PER_CHECKPOINT,
            "training_receipt_sha256": training_receipt,
            "curriculum_digest_sha256": curriculum_digest,
            "population_before_digest_sha256": _population_digest(population_before),
            "population_after_digest_sha256": _population_digest(population_after),
            "training_dataset_seeds": t_seeds,
            "training_model_seeds": m_seeds,
            "scoring_dataset_seeds": q_seeds,
            "model_receipt_count": len(model_receipts),
            "model_receipts_sha256": _sha256(model_receipts),
            "score_cache_hits": cache_hits,
            "score_cache_misses": cache_misses,
            "score_receipt_count": len(score_receipts),
            "score_receipts_sha256": _sha256(score_receipts),
            "shuffle_rng_seed": shuffle_seed,
        }

    if set(indexed) != set(CHECKPOINT_GENERATIONS):
        raise ValueError("Phase-2G provenance checkpoint set drift")
    return [indexed[generation] for generation in CHECKPOINT_GENERATIONS]


def _validate_cell_provenance(
    raw: Mapping[str, Any],
    *,
    arm: str,
    seed: int,
    initial_digest: str,
    terminal_fingerprint: str,
    terminal_classical: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        if int(raw.get("schema_version", -1)) != 1:
            raise ValueError("schema_version")
        if int(raw.get("generation_count", -1)) != GENERATION_COUNT:
            raise ValueError("generation_count")
        if int(raw.get("checkpoint_training_count", -1)) != CHECKPOINT_TRAININGS_PER_CELL:
            raise ValueError("checkpoint_training_count")
        if bool(raw.get("heldout_accessed", True)):
            raise ValueError("heldout_accessed")
        terminal_population_digest = str(raw.get("terminal_population_digest_sha256", ""))
        if not _is_hex64(terminal_population_digest):
            raise ValueError("terminal_population_digest_sha256")

        generation_trace, evaluated, proposal_parents, initial_fingerprints = (
            _validate_generation_trace(
                raw.get("generation_trace"),
                initial_digest=initial_digest,
                terminal_population_digest=terminal_population_digest,
                terminal_fingerprint=terminal_fingerprint,
            )
        )
        classical_ledger = _validate_classical_ledger(
            raw.get("classical_evaluation_ledger"),
            evaluated=evaluated,
            terminal_fingerprint=terminal_fingerprint,
            terminal_classical=terminal_classical,
        )
        parent_map = _validate_parent_map(
            raw.get("parent_map"), proposal_parents=proposal_parents
        )
        lineage = _sequence(raw.get("lineage_diagnostics"), role="lineage diagnostics")
        if not all(isinstance(item, Mapping) for item in lineage):
            raise ValueError("lineage_diagnostics")
        selection_events = _sequence(raw.get("selection_events"), role="selection events")
        if not all(isinstance(item, Mapping) for item in selection_events):
            raise ValueError("selection_events")
        checkpoints = _freeze_checkpoints(
            raw.get("checkpoints"),
            arm=arm,
            seed=seed,
            generation_trace=generation_trace,
            initial_fingerprints=initial_fingerprints,
            evaluated=evaluated,
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and "Phase-2G provenance" in str(exc):
            raise
        raise ValueError(f"Phase-2G provenance validation failed: {exc}") from exc

    provenance = {
        "schema_version": 1,
        "generation_trace_count": len(generation_trace),
        "generation_trace_sha256": _sha256(generation_trace),
        "classical_evaluation_count": len(classical_ledger),
        "classical_evaluation_ledger_sha256": _sha256(classical_ledger),
        "parent_map_count": len(parent_map),
        "parent_map_sha256": _sha256(parent_map),
        "lineage_diagnostics_count": len(lineage),
        "lineage_diagnostics_sha256": _sha256(lineage),
        "selection_event_count": len(selection_events),
        "selection_events_sha256": _sha256(selection_events),
        "terminal_population_digest_sha256": str(raw["terminal_population_digest_sha256"]),
    }
    provenance["provenance_sha256"] = _sha256(provenance)
    return provenance, checkpoints


def _freeze_cell(raw: Mapping[str, Any]) -> dict[str, Any]:
    if str(raw.get("phase", "")) != "2G":
        raise ValueError("terminal cell is not a Phase-2G record")

    seed = int(raw.get("seed", -1))
    arm = str(raw.get("arm", ""))
    if seed not in EVOLUTION_SEEDS or arm not in ARMS:
        raise ValueError("terminal cell has an unfrozen Phase-2G seed/arm")
    if int(raw.get("classical_evaluations", -1)) != CLASSICAL_EVALUATIONS_PER_CELL:
        raise ValueError("Phase-2G classical evaluation budget drift")
    if int(raw.get("checkpoint_trainings", -1)) != CHECKPOINT_TRAININGS_PER_CELL:
        raise ValueError("Phase-2G checkpoint training budget drift")
    if str(raw.get("terminal_selection_rule", "")) != TERMINAL_SELECTION_RULE:
        raise ValueError("Phase-2G terminal selection must remain classical-only")

    initial_digest = str(raw.get("initial_population_digest_sha256", ""))
    if not _is_hex64(initial_digest):
        raise ValueError("Phase-2G initial-population digest is missing or invalid")
    scientific_receipt = _verify_scientific_payload_receipt(raw)
    sbox = validate_sbox(raw.get("terminal_sbox", ()))
    fingerprint = fingerprint_sbox(sbox)
    if str(raw.get("terminal_fingerprint", "")) != fingerprint:
        raise ValueError("Phase-2G terminal fingerprint mismatch")
    classical_payload = _freeze_terminal_classical(raw.get("terminal_classical"))
    provenance, checkpoints = _validate_cell_provenance(
        raw,
        arm=arm,
        seed=seed,
        initial_digest=initial_digest,
        terminal_fingerprint=fingerprint,
        terminal_classical=classical_payload,
    )

    frozen: dict[str, Any] = {
        "seed": seed,
        "arm": arm,
        "classical_evaluations": CLASSICAL_EVALUATIONS_PER_CELL,
        "checkpoint_trainings": CHECKPOINT_TRAININGS_PER_CELL,
        "initial_population_digest_sha256": initial_digest,
        "scientific_payload_sha256": scientific_receipt,
        "provenance": provenance,
        "checkpoints": checkpoints,
        "terminal_selection_rule": TERMINAL_SELECTION_RULE,
        "terminal_fingerprint": fingerprint,
        "terminal_sbox": list(sbox),
        "terminal_classical": classical_payload,
    }
    frozen["cell_manifest_sha256"] = _sha256(frozen)
    return frozen


def _matched_initial_digests_are_valid(
    indexed: Mapping[tuple[int, str], Mapping[str, Any]],
) -> bool:
    for seed in EVOLUTION_SEEDS:
        digests = {
            str(indexed[(int(seed), arm)].get("initial_population_digest_sha256", ""))
            for arm in ARMS
        }
        if len(digests) != 1 or not all(_is_hex64(value) for value in digests):
            return False
    return True


def freeze_phase2g_terminals(
    arm_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate and deterministically freeze all 9-seed × 4-arm terminals."""

    if len(arm_results) != CELL_COUNT:
        raise ValueError("Phase-2G terminal freeze requires exact 9-seed × 4-arm records")

    expected = _expected_cells()
    indexed: dict[tuple[int, str], dict[str, Any]] = {}
    for raw in arm_results:
        if not isinstance(raw, Mapping):
            raise ValueError("Phase-2G arm result must be a mapping")
        frozen = _freeze_cell(raw)
        key = (int(frozen["seed"]), str(frozen["arm"]))
        if key not in expected or key in indexed:
            raise ValueError(f"invalid or duplicate Phase-2G terminal cell {key!r}")
        indexed[key] = frozen

    if set(indexed) != expected:
        raise ValueError("Phase-2G terminal freeze is incomplete")
    if not _matched_initial_digests_are_valid(indexed):
        raise ValueError("Phase-2G matched arms must share one initial-population digest per seed")

    terminals = [indexed[(int(seed), arm)] for seed in EVOLUTION_SEEDS for arm in ARMS]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2G-terminal-freeze",
        "cell_count": CELL_COUNT,
        "evolution_seeds": [int(seed) for seed in EVOLUTION_SEEDS],
        "arms": list(ARMS),
        "classical_evaluations_per_cell": CLASSICAL_EVALUATIONS_PER_CELL,
        "checkpoint_generations": list(CHECKPOINT_GENERATIONS),
        "checkpoint_trainings_per_cell": CHECKPOINT_TRAININGS_PER_CELL,
        "checkpoint_training_count": CELL_COUNT * CHECKPOINT_TRAININGS_PER_CELL,
        "heldout_accessed": False,
        "heldout_training_count": 0,
        "terminal_selection_rule": TERMINAL_SELECTION_RULE,
        "terminals": terminals,
    }
    payload["terminal_freeze_sha256"] = _sha256(payload)
    return payload


def _frozen_checkpoint_summary_is_valid(raw: object) -> bool:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        return False
    rows = list(raw)
    if len(rows) != len(CHECKPOINT_GENERATIONS):
        return False
    for checkpoint_index, (expected_generation, item) in enumerate(
        zip(CHECKPOINT_GENERATIONS, rows)
    ):
        if not isinstance(item, Mapping):
            return False
        if int(item.get("generation", -1)) != expected_generation:
            return False
        if int(item.get("training_count", -1)) != TRAININGS_PER_CHECKPOINT:
            return False
        if not _is_hex64(item.get("training_receipt_sha256", "")):
            return False
        if not _is_hex64(item.get("curriculum_digest_sha256", "")):
            return False
        if not _is_hex64(item.get("population_before_digest_sha256", "")):
            return False
        if not _is_hex64(item.get("population_after_digest_sha256", "")):
            return False
        for field, base in (
            ("training_dataset_seeds", TRAINING_DATASET_BASE_SEEDS),
            ("training_model_seeds", TRAINING_MODEL_BASE_SEEDS),
            ("scoring_dataset_seeds", SCORING_DATASET_BASE_SEEDS),
        ):
            values = item.get(field)
            if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
                return False
            if tuple(int(value) for value in values) != expanded_checkpoint_seed_block(
                base, checkpoint_index
            ):
                return False
        if int(item.get("model_receipt_count", -1)) != TRAININGS_PER_CHECKPOINT:
            return False
        if not _is_hex64(item.get("model_receipts_sha256", "")):
            return False
        if int(item.get("score_cache_hits", -1)) < 0:
            return False
        misses = int(item.get("score_cache_misses", -1))
        if misses < 0 or int(item.get("score_receipt_count", -1)) != misses:
            return False
        if not _is_hex64(item.get("score_receipts_sha256", "")):
            return False
    return True


def _frozen_provenance_is_valid(raw: object) -> bool:
    if not isinstance(raw, Mapping):
        return False
    required_counts = {
        "generation_trace_count": GENERATION_COUNT,
        "classical_evaluation_count": CLASSICAL_EVALUATIONS_PER_CELL,
        "parent_map_count": GENERATION_COUNT * PROPOSALS_PER_GENERATION,
    }
    if int(raw.get("schema_version", -1)) != 1:
        return False
    for field, expected in required_counts.items():
        if int(raw.get(field, -1)) != expected:
            return False
    if int(raw.get("lineage_diagnostics_count", -1)) < 0:
        return False
    if int(raw.get("selection_event_count", -1)) < 0:
        return False
    for field in (
        "generation_trace_sha256",
        "classical_evaluation_ledger_sha256",
        "parent_map_sha256",
        "lineage_diagnostics_sha256",
        "selection_events_sha256",
        "terminal_population_digest_sha256",
        "provenance_sha256",
    ):
        if not _is_hex64(raw.get(field, "")):
            return False
    clean = {key: value for key, value in raw.items() if key != "provenance_sha256"}
    return _sha256(clean) == str(raw["provenance_sha256"])


def heldout_h_authorized(freeze_payload: Mapping[str, Any]) -> bool:
    """Return True only for an intact, complete pre-H terminal freeze manifest."""

    try:
        if int(freeze_payload.get("schema_version", -1)) != 1:
            return False
        if str(freeze_payload.get("phase", "")) != "2G-terminal-freeze":
            return False
        if int(freeze_payload.get("cell_count", -1)) != CELL_COUNT:
            return False
        if tuple(int(v) for v in freeze_payload.get("evolution_seeds", ())) != tuple(
            int(seed) for seed in EVOLUTION_SEEDS
        ):
            return False
        if tuple(str(v) for v in freeze_payload.get("arms", ())) != ARMS:
            return False
        if int(freeze_payload.get("classical_evaluations_per_cell", -1)) != CLASSICAL_EVALUATIONS_PER_CELL:
            return False
        if tuple(int(v) for v in freeze_payload.get("checkpoint_generations", ())) != CHECKPOINT_GENERATIONS:
            return False
        if int(freeze_payload.get("checkpoint_trainings_per_cell", -1)) != CHECKPOINT_TRAININGS_PER_CELL:
            return False
        if int(freeze_payload.get("checkpoint_training_count", -1)) != CELL_COUNT * CHECKPOINT_TRAININGS_PER_CELL:
            return False
        if bool(freeze_payload.get("heldout_accessed", True)):
            return False
        if int(freeze_payload.get("heldout_training_count", -1)) != 0:
            return False
        if str(freeze_payload.get("terminal_selection_rule", "")) != TERMINAL_SELECTION_RULE:
            return False

        terminals = freeze_payload.get("terminals")
        if not isinstance(terminals, Sequence) or isinstance(terminals, (str, bytes, bytearray)):
            return False
        if len(terminals) != CELL_COUNT:
            return False

        seen: set[tuple[int, str]] = set()
        indexed: dict[tuple[int, str], Mapping[str, Any]] = {}
        for item in terminals:
            if not isinstance(item, Mapping):
                return False
            key = (int(item.get("seed", -1)), str(item.get("arm", "")))
            if key not in _expected_cells() or key in seen:
                return False
            seen.add(key)
            indexed[key] = item
            if int(item.get("classical_evaluations", -1)) != CLASSICAL_EVALUATIONS_PER_CELL:
                return False
            if int(item.get("checkpoint_trainings", -1)) != CHECKPOINT_TRAININGS_PER_CELL:
                return False
            if str(item.get("terminal_selection_rule", "")) != TERMINAL_SELECTION_RULE:
                return False
            if not _is_hex64(item.get("initial_population_digest_sha256", "")):
                return False
            if not _is_hex64(item.get("scientific_payload_sha256", "")):
                return False
            if not _frozen_provenance_is_valid(item.get("provenance")):
                return False
            if not _frozen_checkpoint_summary_is_valid(item.get("checkpoints")):
                return False
            sbox = validate_sbox(item.get("terminal_sbox", ()))
            if str(item.get("terminal_fingerprint", "")) != fingerprint_sbox(sbox):
                return False
            if _freeze_terminal_classical(item.get("terminal_classical")) != dict(
                item.get("terminal_classical", {})
            ):
                return False
            stored_cell_sha = str(item.get("cell_manifest_sha256", ""))
            if not _is_hex64(stored_cell_sha):
                return False
            clean_cell = {
                key_: value for key_, value in item.items() if key_ != "cell_manifest_sha256"
            }
            if _sha256(clean_cell) != stored_cell_sha:
                return False

        if seen != _expected_cells() or not _matched_initial_digests_are_valid(indexed):
            return False
        stored = str(freeze_payload.get("terminal_freeze_sha256", ""))
        if not _is_hex64(stored):
            return False
        clean = {
            key: value for key, value in freeze_payload.items() if key != "terminal_freeze_sha256"
        }
        return _sha256(clean) == stored
    except (TypeError, ValueError, KeyError):
        return False
