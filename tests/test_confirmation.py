import pytest

from adversarial_sbox.confirmation import one_sided_sign_test_p


def test_exact_sign_test_known_values():
    assert one_sided_sign_test_p(wins=8, losses=1) == pytest.approx(10 / 512)
    assert one_sided_sign_test_p(wins=7, losses=2) == pytest.approx(46 / 512)
    assert one_sided_sign_test_p(wins=6, losses=0) == pytest.approx(1 / 64)


def test_exact_sign_test_no_non_tied_pairs_is_non_significant():
    assert one_sided_sign_test_p(wins=0, losses=0) == 1.0


def test_exact_sign_test_rejects_negative_counts():
    with pytest.raises(ValueError):
        one_sided_sign_test_p(wins=-1, losses=1)
    with pytest.raises(ValueError):
        one_sided_sign_test_p(wins=1, losses=-1)
