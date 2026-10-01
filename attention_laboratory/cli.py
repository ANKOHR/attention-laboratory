"""Local file CLI. No network, model calls, or GPU dependencies."""
import argparse
import json
import os
from pathlib import Path
import tempfile
from .core import SchemaError, distribution, run, scaling, validate
from .fixtures import generate
from .report import dumps, render, provenance, NOTICE

class ReportWriteError(OSError):
    """Atomic result or report write failed."""

class InputError(ValueError):
    """Named input failure with file and line context."""

def parse_json(value, path, line=1):
    """Reject ambiguous duplicate keys and nonstandard JSON numbers."""
    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                raise ValueError(f"duplicate field {key!r}")
            result[key] = item
        return result

    def constant(value):
        raise ValueError(f"nonstandard number {value}")

    try:
        return json.loads(value, object_pairs_hook=pairs, parse_constant=constant)
    except json.JSONDecodeError as exc:
        raise InputError(f"ParseError: {path}: line {line + exc.lineno - 1}: {exc.msg}") from None
    except ValueError as exc:
        raise InputError(f"ParseError: {path}: line {line}: {exc}") from None

def console(value):
    """Preserve console text using escapes for unsupported or forbidden characters."""
    import sys
    value = value.replace(chr(0x2014), "\\u2014")
    return value.encode(sys.stdout.encoding or "utf-8", "backslashreplace").decode(sys.stdout.encoding or "utf-8")

def load(directory):
    root = Path(directory)
    if not root.is_dir():
        raise InputError(f"MissingInput: {root}; use al fixtures --out <dir>")
    records = []
    for path in sorted(root.iterdir()):
        if path.name in {"expectations.json", "README.md"} or path.is_dir():
            continue
        if path.suffix not in {".jsonl", ".json"}:
            raise InputError(f"SchemaError: {path}: line 1: unsupported input extension {path.suffix}")
        try:
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".jsonl":
                entries = [(line, value) for line, value in enumerate(text.splitlines(), 1) if value.strip() and not value.startswith("#")]
            else:
                entries = [(1, text)]
            for line, value in entries:
                record = parse_json(value, path, line)
                try:
                    validate(record)
                    if any(r["id"] == record["id"] for r in records):
                        raise SchemaError(f"id: duplicate {record['id']!r}")
                except SchemaError as exc:
                    raise InputError(f"SchemaError: {path}: line {line}: {exc}") from None
                records.append(record)
        except UnicodeError as exc:
            raise InputError(f"ParseError: {path}: line 1: invalid UTF-8") from exc
    return records

def atomic_write(path, text):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
        os.replace(temporary, path)
    except OSError as exc:
        raise ReportWriteError(f"ReportWriteError: {path}: {exc}") from None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Exact attention experiments from explicit local inputs")
    sub = parser.add_subparsers(dest="command", required=True)
    fixtures = sub.add_parser("fixtures", help="Generate 200 labelled synthetic records", epilog="Example: al fixtures --out demo")
    fixtures.add_argument("--out", required=True)
    execute = sub.add_parser("run", help="Compute distributions and theoretical scaling", epilog="Example: al run --input demo")
    execute.add_argument("--input", required=True)
    execute.add_argument("--results", default=".al-results.json")
    report = sub.add_parser("report", help="Render exact results with provenance", epilog="Example: al report --format md")
    report.add_argument("--format", choices=["md", "json"], default="md")
    report.add_argument("--results", default=".al-results.json")
    report.add_argument("--out")
    dist = sub.add_parser("distribution", help="Normalize integer attention scores exactly", epilog="Example: al distribution --scores 3,1 --budget 12")
    dist.add_argument("--scores", required=True)
    dist.add_argument("--budget", type=int, default=12)
    scale = sub.add_parser("scaling", help="Count theoretical dense and local attention pairs", epilog="Example: al scaling --tokens 100 --window 4")
    scale.add_argument("--tokens", type=int, required=True)
    scale.add_argument("--window", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 synthetic fixtures.")
        elif args.command == "run":
            result = run(load(args.input))
            atomic_write(args.results, dumps(result))
            print(console(f"Computed {result['summary']['records']} records. Results: {args.results}"))
            print(provenance(result))
            print(NOTICE)
        elif args.command == "report":
            if not Path(args.results).is_file():
                raise InputError(f"MissingInput: {args.results}; run al run --input <dir> first")
            result = parse_json(Path(args.results).read_text(encoding="utf-8"), args.results)
            # Recompute from stored explicit inputs instead of trusting summary figures.
            fields = {"id", "scores", "budget", "window", "synthetic", "source", "date"}
            if not isinstance(result, dict) or not isinstance(result.get("experiments"), list):
                raise InputError(f"SchemaError: {args.results}: line 1: experiments: expected array")
            records = []
            for index, record in enumerate(result["experiments"]):
                if not isinstance(record, dict) or not fields <= record.keys():
                    raise InputError(f"SchemaError: {args.results}: line 1: experiments[{index}]: missing required input fields")
                records.append({key: record[key] for key in fields})
            result = run(records)
            output = render(result, args.format)
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        elif args.command == "distribution":
            try:
                scores = [int(value) for value in args.scores.split(",")]
            except ValueError:
                raise SchemaError("scores: expected comma-separated integers") from None
            print(dumps({"honesty": "Computed from supplied scores; no measured model quality.", **distribution(scores, args.budget)}), end="")
        else:
            print(dumps({"honesty": NOTICE, **scaling(args.tokens, args.window)}), end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        message = f"{type(exc).__name__}: {exc}"
        print(message.encode("ascii", "backslashreplace").decode("ascii"), file=__import__("sys").stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
