# Synthetic examples

These files are generated demonstration data, not real CMG output, measurements, or validated reservoir physics. They are provided under the project's MIT license.

`demo.csv` has 120 points at days 0–119, in three 40-day illustrative cycles. Within each cycle, stage = day % 40:

- Stages 0–9: injection rate = 12 t/day, production = 0; pressure = 20 + 0.30 × stage MPa.
- Stages 10–19: both rates = 0; pressure = 23 − 0.08 × (stage − 10) MPa.
- Stages 20–39: injection = 0; production = 4 × exp(−0.06 × (stage − 20)) t/day; pressure = 22.2 − 0.11 × (stage − 20) MPa.

The discontinuities are illustrative and intentional. No conservation law or calibrated model is claimed. The generator is `make_demo_data()` in `reservoirviz/data.py`.

`field_mapping_example.csv` contains the same synthetic numbers with time in hours and pressure in kPa. It tests manual mapping:

| Field | Source column | Select unit |
|---|---|---|
| Time | ElapsedHours | hour |
| Pressure | BHP_kPa | kPa |
| Injection | Injection | t/day |
| Production | Production | t/day |

After mapping, its normalized values should match `demo.csv` (apart from renamed rate fields).
