import json
from attention_laboratory.fixtures import generate
from attention_laboratory.cli import load
from attention_laboratory.core import run

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    assert (tmp_path / "records.jsonl").read_text().startswith("# Synthetic")
    assert all(r["synthetic"] is True for r in load(tmp_path))
    assert json.loads((tmp_path / "expectations.json").read_text())["synthetic"] is True
    assert "Synthetic" in (tmp_path / "README.md").read_text()

def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    result = run(load(tmp_path))
    expected = json.loads((tmp_path / "expectations.json").read_text())
    assert result["summary"] == expected["summary"]
    assert result["summary"] == {"records": 200, "focused": 100, "tokens": 600, "budget": 2400, "dense_pairs": 2000, "local_pairs": 1400, "mean_concentration": "7/16"}
    assert result["experiments"][0]["weights"] == ["3/4", "1/4"]
    assert result["experiments"][100]["weights"] == ["1/4"]*4

def test_corrupted_fixture_changes_figures(tmp_path):
    generate(tmp_path)
    records = load(tmp_path)
    records[0]["scores"] = [1, 1, 1, 1]
    result = run(records)
    assert result["summary"]["focused"] == 99
    assert result["summary"]["tokens"] == 602
    assert result["summary"]["dense_pairs"] == 2012
