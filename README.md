# Attention Laboratory

A CPU-only Python CLI for repeatable experiments with supplied attention scores and theoretical attention scaling. It normalizes scores, allocates an explicit budget, computes concentration, identifies focused distributions, and counts dense and symmetric local attention pairs. It does not train or run a model. No dependencies beyond Python's standard library are required at runtime. No network calls, GPU libraries, or language-model calls occur.

## Quickstart

Python 3.10 or newer, with setuptools available locally:

```powershell
python -m pip install --no-index --no-deps --no-build-isolation -e .
al fixtures --out demo
al run --input demo
al report --format md
python -m pytest -q
```

Installation uses local files; do not ask pip to download dependencies. Alternatively use `python -m attention_laboratory.cli` in place of `al`. Tests require an existing pytest installation.

If Windows reports that the user Scripts directory is outside PATH, add it to the current shell before using `al`:

```powershell
$alScripts = python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"
$env:Path = "$alScripts;$env:Path"
```

Duplicate JSON fields and nonstandard numbers (`NaN`, `Infinity`) fail with ParseError rather than being silently interpreted. Dates require the ten-character `YYYY-MM-DD` form. Malformed saved results also fail with file and line context.

The fixture demo has 200 synthetic records. A tiny, hand-written five-record synthetic input is included in `examples/five`; use `al run --input examples/five`. The fixture generator always produces the acceptance fixture of 200 records.

## Input format reference

An input directory contains UTF-8 `.jsonl` files with one object per line, or `.json` files with one record object each. JSONL lines beginning with `#` and blank lines are ignored. Files are read in sorted order. Reserved `expectations.json` and `README.md` files are metadata and are ignored. Unsupported extensions fail with a named schema error; CSV and YAML are not accepted. All other record fields are required, with no unknown fields:

```json
{"id":"trial-1","scores":[3,1],"budget":12,"window":1,"synthetic":true,"source":"synthetic example","date":"2026-09-30"}
```

- `id`: unique nonempty string, at most 10000 characters. Duplicates fail.
- `scores`: 1 to 10000 integer scores, each from 0 to 1000000; the total must be positive. Booleans and floats fail. Scores are supplied weights, not logits; softmax is not applied.
- `budget`: integer from 0 to 1000000, representing arbitrary attention units. Fractional allocations are preserved exactly, without rounding or pretending these units are money.
- `window`: integer from 0 to 1000000, the radius of symmetric local attention including self-attention. Boundaries clip the radius to sequence length. This is not causal attention.
- `synthetic`: actual JSON boolean. Use `false` only for Henry's real, manually entered observations.
- `source`: nonempty string of at most 10000 characters. Real records require exactly `Henry entered by hand`. Attribution is self-declared, not independently verified.
- `date`: ISO calendar date no later than the fixed experiment cutoff `2026-09-30`. This stable cutoff avoids clock-dependent output; update the schema deliberately for later trials.

Unicode and Windows paths in strings are supported. JSON backslashes must be escaped. Reports escape Unicode to ASCII JSON sequences to preserve text losslessly and prevent forbidden punctuation in output. Real trial data and results should be stored outside the repository and are not shipped.

## Computation and interpretation

For supplied scores s, weights are s/sum(s); allocation is weight*budget; concentration is sum(weight squared). A record is `focused` if its largest normalized weight is at least 1/2, inclusive. This operational threshold is a definition, not a discovered property or prediction. An empty dataset has zero totals and mean concentration 0 by convention.

For n tokens and radius r=min(window,n-1), dense pair count is n*n and local pair count is n*(2*r+1)-r*(r+1). Empty sequences have zero pairs in the scaling command. Fractions are serialized as strings such as `7/16`, and integers remain integers. Allocation totals reconcile exactly to each budget. Results include every input score and every computed record, making all figures traceable.

## Subcommand catalogue

```powershell
al fixtures --out demo
al run --input demo --results results.json
al report --results results.json --format json --out report.json
al report --results results.json --format md --out report.md
al distribution --scores 3,1 --budget 12
al scaling --tokens 100 --window 4
```

All commands have `--help` and examples. `distribution` supports interactive exploration by rerunning with different explicit scores or budgets. `scaling` supports sequence-length and window experiments. `run` defaults to `.al-results.json` in the current directory; `report` reads it by default. Report rendering recomputes from its stored explicit inputs rather than trusting cached summary totals. Same inputs and options produce byte-identical result/report files. No randomness is used, so no seed is needed. Operational console messages include user-supplied paths.

## Architecture

```text
fixtures.py -> labelled local inputs
                       |
cli.py (parse and validate files) -> core.py (pure exact arithmetic)
                       |                     |
                       +--- atomic results <-+
                                  |
                    report.py -> Markdown / JSON with provenance
```

## Honesty boundary and fixture policy

Every report states the counts of synthetic and self-declared real records. Mixed datasets retain provenance per record. Theoretical pair counts are explicitly labelled and never presented as measured runtime, memory consumption, model quality, prediction, or saved time/money. Distribution figures are computed only from supplied scores. The tool supplies no savings estimate. Benchmark wall-clock times in EVIDENCE.md describe only the named local benchmark, not expected speed on other machines.

The JSONL fixture begins with a synthetic header and every record has `synthetic: true`. The JSON expectations file has a `synthetic: true` field; JSON does not support comments. Fixture Markdown has a synthetic heading. The five-record example follows the same policy. Expectations are independently hand-computed constants; the production engine never reads them.

## Hypothesis, acceptance, and failure modes

Hypothesis: a deterministic CLI whose calculations match planted ground truth gives researchers a trustworthy way to inspect explicit attention distributions and theoretical scaling. The hypothesis concerns computation accuracy, not user adoption or model performance.

Acceptance: all 200 planted cases match exact ground truth, all 100 focused records are identified with zero false positives, budgets and pair counts reconcile, and the complete local fixture demo finishes in under five seconds. Tests corrupt a fixture to prove results are computed. Tests also enumerate attention pairs independently, check empty input, malformed JSON, negative and extreme values, future dates, duplicate IDs, schema drift, Unicode, long strings, Windows paths, deterministic bytes, and atomic write cleanup.

Malformed JSON produces a ParseError naming file and line. Schema errors name file, line and offending field. Missing input gives MissingInput plus a usage hint. Invalid UTF-8 is named. Missing/unwritable output directories and bad destination paths produce ReportWriteError. Atomic replacement prevents partial result/report files and preserves an existing destination on failure. Errors exit 2; successful commands exit 0. Fixture generation is intended for a dedicated directory and overwrites its three named fixture files.

Limitations: inputs are read into memory; validation uses explicit size bounds per record rather than a whole-dataset cap. Exact rational arithmetic is suited to small experiments, not massive model tensors. Source attribution cannot establish authenticity. No measured model behavior is inferred from these fixtures.

## Evidence-based improvement hook and verdict

After two weeks of actual use, record run count and compare computed outputs against a hand-checked sample of real records. Measure error rate as incorrect hand-checked records divided by checked records. Log sample size, erroneous IDs, expected/actual values, dates, and arithmetic in a private trial log; publish only a non-sensitive finding. If error exceeds 10 percent, fix the top failure cause and rerun the sample, or kill the project with the reason. If the tool is not used, record that finding and kill it. Do not fabricate adoption, measured savings, or trial evidence.

The two-week evidence window has not occurred. Final verdict is pending, not asserted from synthetic tests. At review: expand if it earns daily use or revenue; integrate if it overlaps heavily with a sibling; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill if unused or acceptance fails. Record the chosen verdict and evidence in VERDICT.md. See EVIDENCE.md for local acceptance results and LESSONS.md for lessons.
