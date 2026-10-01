"""Synthetic planted cases. No randomness is used or seed required."""
from pathlib import Path
from .report import dumps

EXPECTED = {"records": 200, "focused": 100, "tokens": 600, "budget": 2400,
            "dense_pairs": 2000, "local_pairs": 1400, "mean_concentration": "7/16"}

def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    records = [{"id": f"experiment-{i:03}", "scores": [3, 1] if i < 100 else [1, 1, 1, 1],
                "budget": 12, "window": 1, "synthetic": True,
                "source": "synthetic planted ground truth", "date": "2026-09-30"} for i in range(200)]
    (out / "records.jsonl").write_text("# Synthetic fixtures: all records are synthetic\n" + "".join(__import__("json").dumps(r, sort_keys=True) + "\n" for r in records), encoding="utf-8")
    (out / "expectations.json").write_text(dumps({"synthetic": True, "summary": EXPECTED,
        "focused_ids": [r["id"] for r in records[:100]],
        "derivation": "100*[3,1]: concentration 5/8, pairs 4/4; 100*[1,1,1,1]: concentration 1/4, pairs 16/10. Mean (5/8+1/4)/2=7/16; budgets 200*12=2400."}), encoding="utf-8")
    (out / "README.md").write_text("# Synthetic fixture set\n\nAll records and expectations are synthetic. No measured model performance.\n", encoding="utf-8")
