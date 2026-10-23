from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_demo_renders_data_metrics_and_download_controls():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert [metric.value for metric in app.metric] == ["120", "119 day", "3", "通过"]
    assert len(app.get("plotly_chart")) == 2
    assert len(app.get("download_button")) == 4
    assert app.dataframe[0].value.shape == (120, 4)


def test_upload_mode_waits_for_file_without_crashing():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.radio(key="source_mode").set_value("上传 CSV").run()
    assert not app.exception
    assert any("选择 CSV" in item.value for item in app.info)


def test_deselecting_pressure_renders_only_rates():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    next(item for item in app.selectbox if item.label == "压力列").set_value("— 不使用 —").run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 1
    assert app.metric[2].value == "2"
