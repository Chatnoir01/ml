import hashlib

from adversarial_sbox.datasets import PairSample
from adversarial_sbox.phase1m import _initial_population
from adversarial_sbox.phase2g import (
    SCORING_DATASET_BASE_SEEDS,
    expanded_checkpoint_seed_block,
)
from adversarial_sbox.phase2g_shared_model import (
    INPUT_DIFFERENCES,
    REPLICATES,
    SharedModelState,
    build_shared_training_splits,
    score_candidate_checkpoint,
    train_shared_checkpoint_model,
)


def _fake_pairs(count: int = 400):
    return tuple(
        PairSample(left=2 * i, right=2 * i + 1, label=i % 2)
        for i in range(count)
    )


def test_shared_training_builder_consumes_exact_20x400(monkeypatch):
    import adversarial_sbox.phase2g_shared_model as module

    calls = []

    def fake_generate(_cipher, *, pair_count, input_difference, seed, shuffle=True):
        calls.append((pair_count, input_difference, seed, shuffle))
        return _fake_pairs(pair_count)

    monkeypatch.setattr(module, "generate_balanced_pairs", fake_generate)
    curriculum = _initial_population(726011)
    train, validation, test = build_shared_training_splits(
        curriculum,
        difference=INPUT_DIFFERENCES[0],
        dataset_seed=776003,
    )

    assert (len(train), len(validation), len(test)) == (5600, 1200, 1200)
    assert len(calls) == 20
    assert set(calls) == {(400, INPUT_DIFFERENCES[0], 776003, True)}


def test_checkpoint_training_returns_fresh_checkpoint_scoped_state(monkeypatch):
    import adversarial_sbox.phase2g_shared_model as module

    curriculum = _initial_population(726011)
    fake_train = _fake_pairs(5600)
    fake_validation = _fake_pairs(1200)
    fake_test = _fake_pairs(1200)

    monkeypatch.setattr(
        module,
        "build_shared_training_splits",
        lambda *args, **kwargs: (fake_train, fake_validation, fake_test),
    )
    monkeypatch.setattr(
        module,
        "_fit_shared_model_state_bytes",
        lambda *args, **kwargs: b"deterministic-shared-model",
    )

    state = train_shared_checkpoint_model(
        arm="A",
        evolution_seed=726011,
        checkpoint_generation=5,
        difference=INPUT_DIFFERENCES[0],
        replicate=0,
        curriculum=curriculum,
        dataset_seed=777003,
        model_seed=787009,
    )

    assert state.state_bytes == b"deterministic-shared-model"
    assert state.state_sha256 == hashlib.sha256(state.state_bytes).hexdigest()
    assert state.checkpoint_generation == 5
    assert len(state.curriculum_digest_sha256) == 64


def test_candidate_checkpoint_scoring_is_inference_only_and_uses_exact_q_block(monkeypatch):
    import adversarial_sbox.phase2g_shared_model as module

    calls = []

    def fake_generate(_cipher, *, pair_count, input_difference, seed, shuffle=True):
        calls.append((pair_count, input_difference, seed))
        return _fake_pairs(pair_count)

    def fake_predict(_state, samples):
        return [0.9 if sample.label else 0.1 for sample in samples]

    monkeypatch.setattr(module, "generate_balanced_pairs", fake_generate)
    monkeypatch.setattr(module, "_predict_probabilities", fake_predict)

    models = []
    for difference in INPUT_DIFFERENCES:
        for replicate in range(REPLICATES):
            models.append(
                SharedModelState(
                    arm="A",
                    evolution_seed=726011,
                    checkpoint_generation=5,
                    difference=difference,
                    replicate=replicate,
                    dataset_seed=777003 + replicate,
                    model_seed=787009 + replicate,
                    curriculum_digest_sha256="a" * 64,
                    state_sha256="b" * 64,
                    state_bytes=b"opaque-state",
                )
            )

    candidate = _initial_population(726011)[0]
    receipt = score_candidate_checkpoint(candidate, models=models)

    assert receipt["training_count"] == 0
    assert receipt["model_count"] == 16
    assert receipt["pairs_per_model"] == 400
    assert receipt["neural_advantage"] == 1.0

    q = expanded_checkpoint_seed_block(SCORING_DATASET_BASE_SEEDS, 1)
    assert len(calls) == 16
    for difference in INPUT_DIFFERENCES:
        for replicate, seed in enumerate(q):
            assert (400, difference, seed) in calls
