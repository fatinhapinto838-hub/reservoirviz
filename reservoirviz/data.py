"""CSV parsing, explicit unit handling, and validation, independent of the UI."""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass

import pandas as pd

MAX_FILE_BYTES = 20 * 1024 * 1024
TIME_TO_DAYS = {"day": 1.0, "hour": 1 / 24, "minute": 1 / 1440}
PRESSURE_TO_MPA = {"MPa": 1.0, "kPa": 0.001, "bar": 0.1, "psi": 0.006894757293168}
RATE_UNITS = ("t/day", "kg/day", "Sm³/day", "m³/day (reservoir)", "m³/day (unspecified)", "scf/day", "bbl/day")


class DataError(ValueError):
    """An actionable error in the input or the selected mapping."""


@dataclass(frozen=True)
class ColumnMapping:
    time: str
    time_unit: str
    pressure: str | None = None
    pressure_unit: str | None = None
    injection: str | None = None
    injection_unit: str | None = None
    production: str | None = None
    production_unit: str | None = None


@dataclass
class ParsedCSV:
    frame: pd.DataFrame
    encoding: str
    delimiter: str


@dataclass
class ValidatedData:
    frame: pd.DataFrame
    mapping: ColumnMapping
    warnings: list[str]


def read_csv(
    payload: bytes,
    *,
    encoding: str = "auto",
    delimiter: str = "auto",
    skiprows: int = 0,
    decimal: str = ".",
) -> ParsedCSV:
    """Read one table, reject ambiguous headers, and retain all source columns."""
    if not payload or not payload.strip():
        raise DataError("文件为空，请选择包含表头和至少两行数据的 CSV。")
    if len(payload) > MAX_FILE_BYTES:
        raise DataError("文件超过 20 MB，请先导出单井或单案例数据。")
    if not isinstance(skiprows, int) or not 0 <= skiprows <= 100:
        raise DataError("跳过行数必须为 0–100 的整数。")
    if decimal not in (".", ","):
        raise DataError("小数分隔符只能为点或逗号。")

    if encoding == "auto":
        candidates = ["utf-16"] if payload.startswith((b"\xff\xfe", b"\xfe\xff")) else ["utf-8-sig", "gb18030"]
    else:
        if encoding not in ("utf-8-sig", "gb18030", "utf-16"):
            raise DataError("请选择支持的文本编码。")
        candidates = [encoding]
    text = None
    used_encoding = ""
    for candidate in candidates:
        try:
            text = payload.decode(candidate)
            used_encoding = candidate
            break
        except UnicodeError:
            continue
    if text is None:
        raise DataError("无法解码文件，请尝试 UTF-8、GB18030 或带 BOM 的 UTF-16 CSV。")
    if "\x00" in text:
        raise DataError("检测到空字符，请检查编码或重新导出为文本 CSV。")
    lines = text.splitlines(keepends=True)
    remaining = "".join(lines[skiprows:])
    if not remaining.strip():
        raise DataError("跳过指定行后没有数据，请检查表头所在行。")
    if delimiter == "auto":
        try:
            delimiter = csv.Sniffer().sniff(remaining[:8192], delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
    if delimiter not in (",", ";", "\t", "|"):
        raise DataError("不支持此列分隔符。")
    if delimiter == decimal:
        raise DataError("列分隔符与小数分隔符相同，请明确选择文件的分隔方式。")
    try:
        reader = csv.reader(io.StringIO(remaining), delimiter=delimiter, strict=True)
        headers = next(row for row in reader if row and any(cell.strip() for cell in row))
        headers = [item.strip().lstrip("\ufeff") for item in headers]
        if len(headers) < 2:
            raise DataError("只识别到一列，请检查列分隔符或跳过说明行的数量。")
        if any(not item for item in headers):
            raise DataError("表头包含空列名，请为每列填写名称或移除空列。")
        if len(set(headers)) != len(headers):
            raise DataError("表头存在重复列名，请先给每列设置唯一名称。")
        for number, row in enumerate(reader, start=1):
            if not row or (len(row) == 1 and not row[0].strip()):
                continue
            if len(row) != len(headers):
                raise DataError(f"数据行 {number} 的列数与表头不一致，请检查分隔符或缺失字段。")
        frame = pd.read_csv(io.StringIO(remaining), sep=delimiter, decimal=decimal, on_bad_lines="error", index_col=False)
    except DataError:
        raise
    except (pd.errors.EmptyDataError, pd.errors.ParserError, csv.Error, StopIteration, ValueError) as exc:
        raise DataError("无法解析 CSV，请检查分隔符、引号以及每行的列数。") from exc
    if len(frame.columns) != len(headers):
        raise DataError("表头与数据列数不一致，请检查文件。")
    frame.columns = headers
    if frame.empty:
        raise DataError("文件只有表头或没有有效数据，请提供至少两行数据。")
    return ParsedCSV(frame=frame, encoding=used_encoding, delimiter=delimiter)


def guess_columns(columns: list[str]) -> dict[str, str | None]:
    """Suggest exact known aliases; never infer units from numeric magnitudes."""
    aliases = {
        "time": ("time_days", "time", "days", "time (day)", "时间", "时间(天)"),
        "pressure": ("pressure_mpa", "pressure", "bhp", "pressure (mpa)", "压力", "井底压力"),
        "injection": ("co2_injection_t_day", "injection_rate", "injection", "注入速率", "注入量"),
        "production": ("gas_production_t_day", "production_rate", "production", "产气速率", "产气量"),
    }
    lookup = {name.strip().casefold(): name for name in columns}
    return {key: next((lookup[a] for a in names if a in lookup), None) for key, names in aliases.items()}


def validate_data(source: pd.DataFrame, mapping: ColumnMapping) -> ValidatedData:
    """Normalize time/pressure only. Rate magnitudes and reference conditions persist."""
    if len(source) < 2:
        raise DataError("至少需要两行数据才能绘制时间曲线。")
    if not mapping.time or mapping.time not in source.columns:
        raise DataError("请选择有效的时间列。")
    if mapping.time_unit not in TIME_TO_DAYS:
        raise DataError("请确认时间单位。")
    signals = [("pressure_mpa", mapping.pressure), ("injection_rate", mapping.injection), ("production_rate", mapping.production)]
    if not any(column for _, column in signals):
        raise DataError("请至少选择压力、注入速率或产出速率中的一列。")
    selected = [mapping.time] + [column for _, column in signals if column]
    if len(set(selected)) != len(selected):
        raise DataError("同一源列不能同时对应多个字段，请重新选择。")
    if mapping.pressure and mapping.pressure_unit not in PRESSURE_TO_MPA:
        raise DataError("请确认压力单位。")
    for role in ("injection", "production"):
        if getattr(mapping, role) and getattr(mapping, f"{role}_unit") not in RATE_UNITS:
            raise DataError("请确认每条速率曲线的单位与参考条件。")

    normalized = pd.DataFrame(index=source.index)
    for destination, column in [("time_days", mapping.time)] + signals:
        if not column:
            continue
        if column not in source.columns:
            raise DataError(f"找不到列：{column}")
        if pd.api.types.is_bool_dtype(source[column]):
            raise DataError(f"列「{column}」包含布尔值，请使用数值。")
        values = pd.to_numeric(source[column], errors="coerce")
        invalid = values.isna() | ~values.map(lambda value: math.isfinite(float(value)))
        if invalid.any():
            rows = [str(i + 1) for i, flag in enumerate(invalid) if flag][:5]
            raise DataError(f"列「{column}」存在缺失、非数值或无穷值；数据行：{', '.join(rows)}。请修正原文件。")
        normalized[destination] = values.astype(float)
    normalized["time_days"] *= TIME_TO_DAYS[mapping.time_unit]
    if mapping.pressure:
        normalized["pressure_mpa"] *= PRESSURE_TO_MPA[mapping.pressure_unit]
    # Conversion itself can overflow even if input values are finite.
    if not normalized.map(lambda value: math.isfinite(float(value))).all().all():
        raise DataError("单位换算后的数值超出范围，请检查源数据和单位。")
    if (normalized["time_days"] < 0).any():
        raise DataError("累计时间不能小于零，请检查时间起点或单位。")
    if normalized["time_days"].duplicated().any():
        raise DataError("时间存在重复值。首版仅处理单井/单案例，请先按井或案例拆分，并核对重复记录。")
    warnings = []
    if not normalized["time_days"].is_monotonic_increasing:
        warnings.append("源数据时间未递增，已按时间排序；没有删除、平均或合并记录。")
    normalized = normalized.sort_values("time_days").reset_index(drop=True)
    for column in normalized.columns:
        if column != "time_days" and (normalized[column] < 0).any():
            warnings.append(f"{column} 含负值，已保留原始符号；请确认源软件的流向或压力基准约定。")
    if mapping.injection and mapping.production and mapping.injection_unit != mapping.production_unit:
        warnings.append("注入与产出单位/参考条件不同，使用独立纵轴面板，未做相减或单位换算。")
    return ValidatedData(normalized, mapping, warnings)


def make_demo_data() -> pd.DataFrame:
    """Three 40-day illustrative cycles; not a simulator or a calibrated model."""
    rows = []
    for day in range(120):
        stage = day % 40
        pressure = 20 + 0.30 * stage if stage < 10 else 23 - 0.08 * (stage - 10) if stage < 20 else 22.2 - 0.11 * (stage - 20)
        rows.append({
            "time_days": day,
            "pressure_mpa": round(pressure, 4),
            "co2_injection_t_day": 12.0 if stage < 10 else 0.0,
            "gas_production_t_day": round(4 * math.exp(-0.06 * (stage - 20)), 6) if stage >= 20 else 0.0,
        })
    return pd.DataFrame(rows)
