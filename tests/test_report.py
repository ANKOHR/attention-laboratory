import json
from attention_laboratory.core import run
from attention_laboratory.cli import load
from attention_laboratory.fixtures import generate
from attention_laboratory.report import render

def test_report_matches_ground_truth_exact(tmp_path):
    generate(tmp_path)
    report = json.loads(render(run(load(tmp_path))))
    expected = json.loads((tmp_path / "expectations.json").read_text())
    assert report["summary"] == expected["summary"]

def test_report_zero_false_positives(tmp_path):
    generate(tmp_path)
    report = json.loads(render(run(load(tmp_path))))
    expected = json.loads((tmp_path / "expectations.json").read_text())
    assert [r["id"] for r in report["experiments"] if r["focused"]] == expected["focused_ids"]

def test_report_carries_provenance_banner(tmp_path):
    generate(tmp_path)
    for format in ["md", "json"]:
        output = render(run(load(tmp_path)), format)
        assert "Data provenance: 200 synthetic fixtures; 0 real" in output

def test_hypothetical_figures_labelled():
    for format in ["md", "json"]:
        assert "theoretical" in render(run([]), format)
        assert "not measured runtime" in render(run([]), format)

def test_no_em_dashes_in_outputs(tmp_path):
    generate(tmp_path)
    for format in ["md", "json"]:
        assert chr(0x2014) not in render(run(load(tmp_path)), format)
