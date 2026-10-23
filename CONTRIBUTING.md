# Contributing

Thanks for trying ReservoirViz. Reports from real CSV workflows are welcome.

1. Open an Issue with the problem, expected behavior, software/module, input units, and reproduction steps.
2. Include a minimal synthetic or publishable CSV. Never attach credentials or confidential reservoir data.
3. For code changes, keep parsing/calculation logic in `reservoirviz/` and UI code in `app.py`.
4. Add a focused test when changing validation, conversion, or export behavior. Run `python -m pytest -q`.
5. Explain physical definitions and assumptions before adding numerical calculations.

AI-assisted contributions are welcome. Review and understand the proposed code, respect dependency licenses, and report what was actually run. Avoid invented validation claims, generated community activity, or unverified physics.

## Local development

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m streamlit run app.py --server.address=127.0.0.1
```

Keep changes small enough to review, and include screenshots when changing the interface.
