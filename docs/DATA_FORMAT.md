# CSV and unit contract

Version 0.1.0 accepts one single-well or single-case table with one header row and at least two data rows. Elapsed times must be numeric, nonnegative, finite, and unique. Multiple wells/cases must be split before loading.

The required mapping is a time column plus at least one signal. Extra source columns are visible in the preview and excluded from the normalized export. Column names must be nonempty and unique after trimming whitespace.

| Output field | Input | Output units |
|---|---|---|
| `time_days` | Elapsed time in day, hour, or minute | day |
| `pressure_mpa` | Optional pressure in MPa, kPa, bar, or psi | MPa |
| `injection_rate` | Optional numeric rate | Unchanged; stored in metadata |
| `production_rate` | Optional numeric rate | Unchanged; stored in metadata |

Pressure factors to MPa: MPa × 1, kPa × 0.001, bar × 0.1, psi × 0.006894757293168. These convert pressure units only; they do not change gauge/absolute pressure reference.

Rate labels include t/day, kg/day, Sm³/day, m³/day at reservoir conditions, m³/day with unspecified conditions, scf/day, and bbl/day. They label source values without converting between units. `Sm³` and `scf` reference conditions are supplied by the source, not standardized or inferred by this app. The v0.1 metadata does not encode reference temperature/pressure as structured fields; preserve the original case documentation alongside exports.

Selected values must be numeric and finite. Invalid rows are rejected with positional data-row hints rather than silently removed. The file reader rejects inconsistent row widths and duplicate headers. Time is sorted in ascending order with a notice. Negative signal values are retained with a notice because source sign conventions and pressure reference may differ.

Supported input encodings: UTF-8 (with or without BOM), GB18030, and BOM-marked UTF-16 (automatic detection). Delimiters: comma, semicolon, tab, pipe. Decimal mark: dot or comma; the decimal mark must differ from the delimiter. UTF-16 without BOM is not auto-detected. Auto-detection is heuristic: inspect the preview and explicitly select settings if needed.

Downloads:

- Normalized CSV: UTF-8 with BOM, numeric values only, selected fields only.
- Metadata JSON: source filename and SHA-256, mapping, original and normalized units, parsing settings, notices, synthetic-demo flag and provenance status. The flag is true only for the built-in example; false does not establish that an uploaded file is real or validated.
- HTML report: Plotly JavaScript embedded inline, figures, and escaped metadata. Internet access is not required to load its charts.

No time resampling, smoothing, rate integration, component balance, storage accounting, or reservoir simulation is performed. The source file is never modified.
