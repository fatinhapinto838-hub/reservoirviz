from dataclasses import replace

from reservoirviz.charts import html_report, make_charts
from reservoirviz.data import make_demo_data, validate_data
from test_data import DEMO_MAPPING


def test_different_rate_units_get_distinct_y_axes():
    data = validate_data(make_demo_data(), replace(DEMO_MAPPING, production_unit="Sm³/day"))
    chart = make_charts(data)["rates"]
    assert [trace.yaxis for trace in chart.data] == ["y", "y2"]
    assert "t/day" in chart.layout.yaxis.title.text
    assert "Sm³/day" in chart.layout.yaxis2.title.text


def test_same_rate_units_share_axis_and_retain_values():
    data = validate_data(make_demo_data(), DEMO_MAPPING)
    chart = make_charts(data)["rates"]
    assert list(chart.data[0].y) == data.frame.injection_rate.tolist()
    assert chart.layout.yaxis.title.text == "Rate (t/day)"


def test_html_contains_inline_plotly_and_escaped_metadata():
    charts = make_charts(validate_data(make_demo_data(), DEMO_MAPPING))
    report = html_report(charts, {"source_file": "<script>alert(1)</script>", "synthetic_demo": True})
    assert "plotly.js" in report
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in report
    assert 'src="https://cdn.plot.ly' not in report
    assert "Pressure history" in report
    assert "Injection & production rates" in report
