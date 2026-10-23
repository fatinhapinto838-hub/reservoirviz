# Initial validation — 2026-10-23

## Environment

- macOS, Apple Silicon (arm64).
- Python 3.12.14, Streamlit 1.66.0, pandas 3.1.0, Plotly 6.9.0.
- Validation dependencies were installed into a separate local environment outside this source folder.

## Completed checks

- `python -m pytest -q`: **29 passed**.
- Data tests: UTF-8/GB18030/UTF-16, alternate separators and decimal marks, metadata-row skipping, duplicate/empty headers, inconsistent row widths, missing/nonfinite numbers, duplicate/negative elapsed time, one-row rejection, explicit units, psi conversion, sorting, and preserved signed rates.
- Export tests: independent rate axes when units differ, unchanged rate values, embedded Plotly JavaScript, escaped report metadata.
- Streamlit AppTest: demo metrics/data/charts/download controls; upload mode without a file; optional pressure removal.
- Actual local server startup and browser rendering with synthetic demonstration data.
- Actual browser upload of `field_mapping_example.csv`, followed by manual time/pressure/rate mapping: hour → day and kPa → MPa.
- Actual browser downloads of HTML, normalized CSV, and metadata JSON. All 120 normalized rows were compared with the expected demo values; field units and source SHA-256 matched.
- Desktop and narrow-pane display were inspected. The screenshots in this repository are actual running UI captures using synthetic data.
- The exported HTML includes inline Plotly code and no Plotly CDN script dependency. Browser download succeeded; fully offline rendering was not separately exercised with networking disabled.

## Boundaries

- No real user CMG export has been supplied or validated. The mapping example is synthetic and must not be described as a verified CMG adapter.
- Windows launcher execution and Windows rendering were not tested on a Windows machine.
- GitHub Actions configuration is included, but no remote CI result, GitHub release, public deployment, or external user adoption is claimed.
- Physics, cumulative quantities, component accounting, and CO₂ storage calculations are not implemented or validated.
- Convenience launchers require an installed, supported Python interpreter. The first dependency installation needs internet access.

Use permitted real exports and independent manual checks before relying on the tool in research. Preserve source units, sign conventions, pressure reference, and standard-volume conditions.
