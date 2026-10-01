import json
import subprocess
import sys
import time
import pytest
from attention_laboratory.cli import main, load, InputError
from attention_laboratory.fixtures import generate

def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    start = time.perf_counter()
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md"]) == 0
    assert time.perf_counter()-start < 5
    assert "Data provenance" in capsys.readouterr().out

def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty").mkdir()
    assert main(["run", "--input", "empty"]) == 0
    assert main(["report", "--format", "json"]) == 0
    assert '"records": 0' in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "bad.jsonl").write_text("# comment\n{broken", encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "bad.jsonl: line 2" in error
    assert "Traceback" not in error

def test_determinism_byte_identical(tmp_path):
    generate(tmp_path / "demo")
    path = tmp_path / "result.json"
    args = ["run", "--input", str(tmp_path / "demo"), "--results", str(path)]
    assert main(args) == 0
    first = path.read_bytes()
    assert main(args) == 0
    assert first == path.read_bytes()
    for format in ["json", "md"]:
        out = tmp_path / f"report.{format}"
        args = ["report", "--results", str(path), "--format", format, "--out", str(out)]
        assert main(args) == 0
        first = out.read_bytes()
        assert main(args) == 0
        assert out.read_bytes() == first

def test_cli_smoke_all_subcommands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for command in ["fixtures", "run", "report", "distribution", "scaling"]:
        with pytest.raises(SystemExit) as error:
            main([command, "--help"])
        assert error.value.code == 0
    assert main(["distribution", "--scores", "3,1"]) == 0
    assert main(["scaling", "--tokens", "4", "--window", "1"]) == 0
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "json"]) == 0

def test_handles_unicode_and_long_inputs(tmp_path, capsys):
    generate(tmp_path)
    record = load(tmp_path)[0]
    record["id"] = "研究" + "x"*9998
    record["source"] = "C:\\Users\\Henry\\研究" + chr(0x2014)
    (tmp_path / "records.jsonl").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    results = tmp_path.parent / "unicode-results.json"
    assert main(["run", "--input", str(tmp_path), "--results", str(results)]) == 0
    assert main(["report", "--results", str(results)]) == 0
    output = capsys.readouterr().out
    assert chr(0x2014) not in output
    assert json.loads(results.read_text())["experiments"][0]["id"] == record["id"]

@pytest.mark.parametrize("field,value", [("date", "2026-10-01"), ("budget", -1), ("id", "x"*10001), ("synthetic", "true"), ("scores", [0]), ("extra", 1)])
def test_schema_errors_name_field(tmp_path, capsys, field, value):
    generate(tmp_path)
    record = load(tmp_path)[0]
    record[field] = value
    (tmp_path / "records.jsonl").write_text(json.dumps(record))
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "SchemaError" in error and (field in error or "fields" in error)

def test_duplicate_ids_rejected(tmp_path):
    generate(tmp_path)
    record = load(tmp_path)[0]
    (tmp_path / "records.jsonl").write_text((json.dumps(record)+"\n")*2)
    with pytest.raises(InputError, match="duplicate"):
        load(tmp_path)

def test_missing_input_and_write_failure(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err
    generate(tmp_path / "demo")
    results = tmp_path / "results.json"
    assert main(["run", "--input", str(tmp_path / "demo"), "--results", str(results)]) == 0
    destination = tmp_path / "directory"
    destination.mkdir()
    before = set(tmp_path.iterdir())
    assert main(["report", "--results", str(results), "--out", str(destination)]) == 2
    assert set(tmp_path.iterdir()) == before
    assert "Traceback" not in capsys.readouterr().err

def test_real_provenance_and_five_record_input(tmp_path, capsys):
    generate(tmp_path / "synthetic")
    records = load(tmp_path / "synthetic")[:5]
    real = tmp_path / "real"
    real.mkdir()
    for record in records:
        record["synthetic"] = False
        record["source"] = "Henry entered by hand"
    (real / "records.jsonl").write_text("\n".join(json.dumps(r) for r in records))
    results = tmp_path / "result.json"
    assert main(["run", "--input", str(real), "--results", str(results)]) == 0
    assert main(["report", "--results", str(results)]) == 0
    assert "0 synthetic fixtures; 5 real records" in capsys.readouterr().out

def test_module_entrypoint():
    process = subprocess.run([sys.executable, "-m", "attention_laboratory.cli", "distribution", "--scores", "3,1"], capture_output=True, text=True)
    assert process.returncode == 0
    assert json.loads(process.stdout)["weights"] == ["3/4", "1/4"]

@pytest.mark.parametrize("text", ['{"id":"one","id":"two"}', '{"scores":[NaN]}', '{"scores":[Infinity]}'])
def test_ambiguous_json_rejected(tmp_path, capsys, text):
    (tmp_path / "bad.jsonl").write_text(text, encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    assert "ParseError" in capsys.readouterr().err

@pytest.mark.parametrize("text", ['{broken', '[]', '{"experiments": [null]}', '{"experiments": [{}]}'])
def test_malformed_results_named_error(tmp_path, capsys, text):
    result = tmp_path / "results.json"
    result.write_text(text, encoding="utf-8")
    assert main(["report", "--results", str(result)]) == 2
    error = capsys.readouterr().err
    assert "results.json: line 1" in error
    assert "Traceback" not in error

def test_run_path_punctuation_escaped(tmp_path, capsys):
    generate(tmp_path / "demo")
    result = tmp_path / ("result" + chr(0x2014) + ".json")
    assert main(["run", "--input", str(tmp_path / "demo"), "--results", str(result)]) == 0
    output = capsys.readouterr().out
    assert chr(0x2014) not in output
    assert "200 synthetic fixtures" in output
