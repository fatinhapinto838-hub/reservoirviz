from dataclasses import replace

import pandas as pd
import pytest

from reservoirviz.data import ColumnMapping, DataError, make_demo_data, read_csv, validate_data

DEMO_MAPPING = ColumnMapping("time_days", "day", "pressure_mpa", "MPa", "co2_injection_t_day", "t/day", "gas_production_t_day", "t/day")


@pytest.mark.parametrize("encoding", ["utf-8-sig", "gb18030", "utf-16"])
def test_text_encodings_preserve_chinese_headers(encoding):
    parsed = read_csv("时间,压力\n0,20\n1,21\n".encode(encoding))
    assert parsed.frame.columns.tolist() == ["时间", "压力"]
    assert parsed.frame.iloc[1, 1] == 21


def test_metadata_lines_semicolon_and_decimal_comma():
    result = read_csv(b"case demo\nTime;BHP\n0;20,5\n24;21,5\n", skiprows=1, delimiter=";", decimal=",")
    data = validate_data(result.frame, ColumnMapping("Time", "hour", "BHP", "bar"))
    assert data.frame.time_days.tolist() == [0, 1]
    assert data.frame.pressure_mpa.tolist() == pytest.approx([2.05, 2.15])


@pytest.mark.parametrize("content", [b"", b" \n", b"t,p\n", b"t,p\n0,20,extra\n1,21\n", b"t,p\n0\n1,21\n", b"t, t\n0,1\n1,2\n", b"t,\n0,1\n1,2\n"])
def test_empty_ambiguous_and_ragged_files_are_rejected(content):
    with pytest.raises(DataError):
        read_csv(content)


@pytest.mark.parametrize("value", [None, "bad", float("inf"), float("-inf")])
def test_missing_or_nonfinite_selected_values_are_rejected(value):
    frame = pd.DataFrame({"t": [0, 1], "p": [20, value]})
    with pytest.raises(DataError, match="数据行：2"):
        validate_data(frame, ColumnMapping("t", "day", "p", "MPa"))


@pytest.mark.parametrize("times", [[0, 0], [-1, 0]])
def test_duplicate_and_negative_times_are_rejected(times):
    with pytest.raises(DataError):
        validate_data(pd.DataFrame({"t": times, "p": [20, 21]}), ColumnMapping("t", "day", "p", "MPa"))


def test_one_row_and_unconfirmed_units_are_rejected():
    with pytest.raises(DataError, match="两行"):
        validate_data(pd.DataFrame({"t": [0], "p": [20]}), ColumnMapping("t", "day", "p", "MPa"))
    with pytest.raises(DataError, match="压力单位"):
        validate_data(pd.DataFrame({"t": [0, 1], "p": [20, 21]}), ColumnMapping("t", "day", "p", None))


def test_time_pressure_conversion_and_sorting_preserve_correspondence():
    frame = pd.DataFrame({"t": [24, 0], "p": [2000, 1000], "rate": [7, 9]})
    mapping = ColumnMapping("t", "hour", "p", "kPa", "rate", "kg/day")
    result = validate_data(frame, mapping)
    assert result.frame.to_dict("list") == {"time_days": [0.0, 1.0], "pressure_mpa": [1.0, 2.0], "injection_rate": [9.0, 7.0]}
    assert any("排序" in warning for warning in result.warnings)


def test_psi_conversion():
    result = validate_data(pd.DataFrame({"t": [0, 1], "p": [0, 1000]}), ColumnMapping("t", "day", "p", "psi"))
    assert result.frame.pressure_mpa.iloc[1] == pytest.approx(6.894757293168)


def test_signed_rates_preserved_and_mixed_units_warn():
    frame = pd.DataFrame({"t": [0, 1], "i": [-12, 0], "p": [0, 1000]})
    result = validate_data(frame, ColumnMapping("t", "day", injection="i", injection_unit="t/day", production="p", production_unit="Sm³/day"))
    assert result.frame.injection_rate.tolist() == [-12, 0]
    assert result.frame.production_rate.tolist() == [0, 1000]
    assert len(result.warnings) == 2


def test_reusing_one_column_as_multiple_quantities_is_rejected():
    with pytest.raises(DataError, match="同时对应"):
        validate_data(make_demo_data(), replace(DEMO_MAPPING, injection="pressure_mpa"))


def test_demo_is_three_complete_cycles_and_contains_no_missing_values():
    source = make_demo_data()
    result = validate_data(source, DEMO_MAPPING)
    assert len(result.frame) == 120
    assert result.frame.time_days.tolist() == list(range(120))
    assert (source.co2_injection_t_day > 0).sum() == 30
    assert (source.gas_production_t_day > 0).sum() == 60
    assert result.warnings == []
