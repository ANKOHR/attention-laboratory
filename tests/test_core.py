import pytest
from attention_laboratory.core import distribution, scaling, run, SchemaError

def test_exact_distribution():
    assert distribution([3, 1]) == {"weights": ["3/4", "1/4"], "allocation": ["9", "3"], "concentration": "5/8", "focused": True}

def test_scaling_matches_enumeration():
    for n in range(20):
        for w in range(25):
            assert scaling(n, w)["local_pairs"] == sum(abs(i-j) <= w for i in range(n) for j in range(n))

@pytest.mark.parametrize("scores,budget", [([-1, 2], 12), ([0, 0], 12), ([True], 12), ([1], -1), ([1000001], 12), ([], 12), ([1.5], 12)])
def test_rejects_adversarial_values(scores, budget):
    with pytest.raises(SchemaError):
        distribution(scores, budget)

def test_allocations_reconcile_exactly():
    from fractions import Fraction
    for scores in ([3, 7, 11], [0, 1], [1] * 101):
        assert sum(map(Fraction, distribution(scores, 17)["allocation"])) == 17
