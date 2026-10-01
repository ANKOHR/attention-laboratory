"""Reports explicitly distinguish supplied data from theoretical figures."""
import json

NOTICE = "Pair counts are theoretical mathematical counts, not measured runtime, memory, model quality, or time/money saved."

def dumps(value):
    # ASCII escaping preserves Unicode and excludes forbidden punctuation in output.
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n"

def provenance(result):
    synthetic = sum(r["synthetic"] for r in result["experiments"])
    real = len(result["experiments"]) - synthetic
    return f"Data provenance: {synthetic} synthetic fixtures; {real} real records attributed to Henry, entered by hand (self-declared, not independently verified)."

def render(result, format="json"):
    banner = provenance(result)
    document = {"provenance": banner, "honesty": NOTICE, **result}
    if format == "json":
        return dumps(document)
    if format != "md":
        raise ValueError("format: expected md or json")
    return "# Attention Laboratory\n\n" + banner + "\n\n" + NOTICE + "\n\nComputed summary (exact fractions):\n\n" + "\n".join(f"- {key}: {value}" for key, value in result["summary"].items()) + "\n\nPer-record trace, including explicit inputs:\n\n```json\n" + dumps(result["experiments"]) + "```\n"
