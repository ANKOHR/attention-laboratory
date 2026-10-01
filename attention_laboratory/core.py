"""Pure exact arithmetic. Pair counts are theoretical, never runtime estimates."""
from fractions import Fraction
from datetime import date

class SchemaError(ValueError):
    """An explicit input contract violation."""

def integer(value, field, minimum=0, maximum=1000000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise SchemaError(f"{field}: expected integer in [{minimum}, {maximum}]")
    return value

def scaling(tokens, window):
    integer(tokens, "tokens")
    integer(window, "window")
    radius = min(window, max(0, tokens - 1))
    return {"dense_pairs": tokens * tokens,
            "local_pairs": tokens * (2 * radius + 1) - radius * (radius + 1)}

def distribution(scores, budget=12):
    if not isinstance(scores, list) or not 1 <= len(scores) <= 10000:
        raise SchemaError("scores: expected 1 to 10000 nonnegative integer scores")
    for score in scores:
        integer(score, "scores")
    integer(budget, "budget")
    if not sum(scores):
        raise SchemaError("scores: total must be positive")
    total = sum(scores)
    weights = [Fraction(score, total) for score in scores]
    concentration = sum((w*w for w in weights), Fraction())
    return {"weights": [str(w) for w in weights],
            "allocation": [str(w * budget) for w in weights],
            "concentration": str(concentration),
            "focused": max(weights) >= Fraction(1, 2)}

def validate(record):
    required = {"id", "scores", "budget", "window", "synthetic", "source", "date"}
    if not isinstance(record, dict):
        raise SchemaError("record: expected object")
    if set(record) != required:
        raise SchemaError(f"fields: missing {sorted(required-set(record))}, unknown {sorted(set(record)-required)}")
    for field in ("id", "source"):
        if not isinstance(record[field], str) or not 1 <= len(record[field]) <= 10000:
            raise SchemaError(f"{field}: expected nonempty string of at most 10000 characters")
    if type(record["synthetic"]) is not bool:
        raise SchemaError("synthetic: expected boolean")
    if not record["synthetic"] and record["source"] != "Henry entered by hand":
        raise SchemaError("source: real records require 'Henry entered by hand' attribution")
    try:
        if not isinstance(record["date"], str) or len(record["date"]) != 10:
            raise ValueError()
        parsed = date.fromisoformat(record["date"])
    except (ValueError, TypeError):
        raise SchemaError("date: expected ISO date") from None
    if parsed > date(2026, 9, 30):
        raise SchemaError("date: later than fixed experiment cutoff 2026-09-30")
    distribution(record["scores"], record["budget"])
    integer(record["window"], "window")
    return record

def run(records):
    seen = set()
    experiments = []
    for record in records:
        validate(record)
        if record["id"] in seen:
            raise SchemaError(f"id: duplicate {record['id']!r}")
        seen.add(record["id"])
        experiments.append({"id": record["id"], "source": record["source"],
                            "synthetic": record["synthetic"], "date": record["date"],
                            "scores": record["scores"], "budget": record["budget"],
                            "window": record["window"], "tokens": len(record["scores"]),
                            **distribution(record["scores"], record["budget"]),
                            **scaling(len(record["scores"]), record["window"])})
    experiments.sort(key=lambda r: r["id"])
    count = len(experiments)
    return {"experiments": experiments, "summary": {
        "records": count, "focused": sum(r["focused"] for r in experiments),
        "tokens": sum(r["tokens"] for r in experiments),
        "budget": sum(r["budget"] for r in experiments),
        "dense_pairs": sum(r["dense_pairs"] for r in experiments),
        "local_pairs": sum(r["local_pairs"] for r in experiments),
        "mean_concentration": str(sum((Fraction(r["concentration"]) for r in experiments), Fraction()) / count) if count else "0"}}
