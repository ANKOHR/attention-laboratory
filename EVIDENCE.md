# Local acceptance evidence

Measured on 2026-10-01 on this Windows machine with Python 3.12.10, CPU only.
No network, GPU workload, or language-model calls were used.

`python -m pytest -q`: 42 passed in 1.27 seconds.

The installed executable completed `al fixtures --out demo`,
`al run --input demo`, and `al report --format md --out demo/report.md`
in 0.9707863 seconds combined, measured with System.Diagnostics.Stopwatch.
This is a local wall-clock measurement, not an expected speed or time savings.
The hand-written five-record example also ran and rendered successfully.

Exact synthetic ground truth verified by tests:

| Quantity | Expected and computed |
| --- | --- |
| Records | 200 |
| Focused records | 100 |
| False positives | 0 |
| Tokens | 600 |
| Attention budget units | 2400 |
| Theoretical dense pairs | 2000 |
| Theoretical local pairs | 1400 |
| Mean concentration | 7/16 |

The independent oracle uses 100 distributions [3,1] and 100 distributions
[1,1,1,1]. Concentrations are 5/8 and 1/4; their mean is 7/16.
Dense counts per record are 4 and 16; local counts are 4 and 10.
All figures come from synthetic inputs, not observed model behavior.

Adversarial evidence includes mutated scores changing the reported totals,
independent pair enumeration, exact budget reconciliation, duplicate IDs,
duplicate JSON fields, nonstandard numbers, empty inputs, schema errors,
malformed saved results, Unicode, long strings, and failed atomic writes.
Deterministic results and both report formats are checked byte for byte.

No real-use accuracy sample, adoption, revenue, or saved time was measured.
The two-week improvement hook and final verdict remain pending in VERDICT.md.
