"""Run with: python -m streamlit run app.py"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
import streamlit as st

from reservoirviz import __version__
from reservoirviz.charts import html_report, make_charts
from reservoirviz.data import (
    PRESSURE_TO_MPA, RATE_UNITS, TIME_TO_DAYS, ColumnMapping, DataError,
    guess_columns, make_demo_data, read_csv, validate_data,
)

st.set_page_config(page_title="ReservoirViz · 油藏时序分析", page_icon="💧", layout="wide")
st.markdown("""<style>
.block-container{max-width:1280px;padding-top:4.5rem;padding-bottom:3rem}
h1{letter-spacing:-1.6px!important;font-size:2.6rem!important;padding:0 0 .5rem!important}h2,h3{letter-spacing:-.4px}
.rv-kicker{font-size:12px;letter-spacing:2px;font-weight:700;color:#0b8a80;margin:0 0 6px}
.rv-intro{font-size:17px;color:#607382;max-width:760px;margin-bottom:4px}
.rv-badge{display:inline-block;background:#e4f3f0;color:#086c64;border-radius:6px;padding:4px 10px;font-size:12px;margin:0 6px 4px 0}
[data-testid="stMetric"]{background:#fff;border:1px solid #e5ecef;border-radius:12px;padding:18px}
[data-testid="stSidebar"]{border-right:1px solid #e2e9ed}
footer{visibility:hidden}
</style>""", unsafe_allow_html=True)

st.markdown('<div class="rv-kicker">RESERVOIR TIME SERIES · OPEN SOURCE</div>', unsafe_allow_html=True)
st.title("ReservoirViz")
st.markdown('<div class="rv-intro">从模拟导出的 CSV 到清晰的压力与注采曲线。核对字段和单位，保留可追溯的数据与图表。</div>', unsafe_allow_html=True)
st.markdown(f'<span class="rv-badge">v{__version__}</span><span class="rv-badge">单井 / 单案例</span><span class="rv-badge">本地分析</span>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 数据工作台")
    mode = st.radio("数据来源", ["演示数据", "上传 CSV"], key="source_mode")
    st.download_button("下载演示 CSV", make_demo_data().to_csv(index=False).encode("utf-8-sig"), "reservoirviz_demo.csv", "text/csv", width="stretch", key="download_demo")
    st.caption("演示文件为人工合成数据，用于体验流程。")
    uploaded = st.file_uploader("上传 CSV", type=["csv"], key="csv_upload") if mode == "上传 CSV" else None
    with st.expander("CSV 读取设置", expanded=False):
        separator_label = st.selectbox("列分隔符", ["自动识别", "逗号 ,", "分号 ;", "制表符 Tab", "竖线 |"], key="separator")
        encoding_label = st.selectbox("文本编码", ["自动识别", "UTF-8", "GB18030", "UTF-16"], key="encoding")
        skiprows = st.number_input("跳过文件开头的说明行", min_value=0, max_value=100, value=0, step=1, key="skiprows")
        decimal_label = st.selectbox("小数分隔符", ["点 .", "逗号 ,"], key="decimal")
    st.caption("支持一个表头行、数值累计时间；每份文件最大 20 MB。")

is_demo = mode == "演示数据"
if not is_demo and uploaded is None:
    st.info("请在左侧选择 CSV。先按井或案例拆分数据，保留表头和单位说明。")
    st.markdown("**操作流程**　上传文件 → 对应字段 → 确认单位 → 检查曲线 → 导出结果")
    st.stop()

payload = make_demo_data().to_csv(index=False).encode("utf-8-sig") if is_demo else uploaded.getvalue()
source_name = "reservoirviz_demo.csv" if is_demo else uploaded.name
parsing = {
    "encoding": {"自动识别": "auto", "UTF-8": "utf-8-sig", "GB18030": "gb18030", "UTF-16": "utf-16"}[encoding_label],
    "delimiter": {"自动识别": "auto", "逗号 ,": ",", "分号 ;": ";", "制表符 Tab": "\t", "竖线 |": "|"}[separator_label],
    "skiprows": int(skiprows), "decimal": "." if decimal_label == "点 ." else ",",
}
# Demo always uses the bundled, known CSV format.
if is_demo:
    parsing = {"encoding": "auto", "delimiter": ",", "skiprows": 0, "decimal": "."}
try:
    parsed = read_csv(payload, **parsing)
except DataError as exc:
    st.error(str(exc))
    st.caption("可调整左侧读取设置后重试，原始文件不会被修改。")
    st.stop()

columns = list(parsed.frame.columns)
suggestions = guess_columns(columns)
source_id = hashlib.sha256(payload + json.dumps(parsing, sort_keys=True).encode()).hexdigest()[:12]
NONE = "— 不使用 —"
UNKNOWN = "— 请选择单位 —"


def column_picker(label: str, role: str, required: bool = False) -> str | None:
    options = columns if required else [NONE] + columns
    default = suggestions[role]
    selection = st.selectbox(label, options, index=options.index(default) if default in options else 0, key=f"{source_id}_{role}")
    return None if selection == NONE else selection


def unit_picker(label: str, role: str, options: list[str], selected_column: str | None, known: dict[str, str]) -> str | None:
    values = [UNKNOWN] + options
    default = known.get(selected_column, UNKNOWN)
    # Include the selected column in the key to prevent a previous column's unit carrying over.
    selection = st.selectbox(label, values, index=values.index(default), key=f"{source_id}_{role}_{selected_column}", disabled=selected_column is None)
    return None if selection == UNKNOWN or selected_column is None else selection


with st.sidebar:
    st.divider()
    st.markdown("### 字段与单位")
    st.caption("相似列名只是建议；请按源软件说明核对。")
    time_col = column_picker("时间列（必选）", "time", required=True)
    time_unit = unit_picker("源时间单位", "time_unit", list(TIME_TO_DAYS), time_col, {"time_days": "day", "days": "day"})
    pressure_col = column_picker("压力列", "pressure")
    pressure_unit = unit_picker("源压力单位", "pressure_unit", list(PRESSURE_TO_MPA), pressure_col, {"pressure_mpa": "MPa"})
    injection_col = column_picker("注入速率列", "injection")
    injection_unit = unit_picker("注入速率单位", "injection_unit", list(RATE_UNITS), injection_col, {"co2_injection_t_day": "t/day"})
    production_col = column_picker("产出速率列", "production")
    production_unit = unit_picker("产出速率单位", "production_unit", list(RATE_UNITS), production_col, {"gas_production_t_day": "t/day"})
    st.caption("时间统一为 day，压力统一为 MPa。速率数值与参考条件保持原样。Sm³ 的标准条件需以源软件设置为准。")

mapping = ColumnMapping(time_col, time_unit, pressure_col, pressure_unit, injection_col, injection_unit, production_col, production_unit)
try:
    data = validate_data(parsed.frame, mapping)
except DataError as exc:
    st.warning(str(exc))
    st.markdown("#### 原始数据预览")
    st.dataframe(parsed.frame.head(30), width="stretch", hide_index=True)
    st.stop()

if is_demo:
    st.info("当前为合成演示数据：三个示意周期，共 120 个数据点；不代表真实储层或 CMG 模拟结果。")
else:
    st.success(f"已读取 {source_name}。请在「数据与检查」中核对源文件与单位。")

frame = data.frame
metrics = st.columns(4)
metrics[0].metric("数据点", f"{len(frame):,}")
metrics[1].metric("时间跨度", f"{frame.time_days.iloc[-1] - frame.time_days.iloc[0]:g} day")
metrics[2].metric("曲线数量", str(len(frame.columns) - 1))
metrics[3].metric("检查结果", "有提示" if data.warnings else "通过")

charts = make_charts(data)
plot_tab, data_tab, export_tab = st.tabs(["曲线分析", "数据与检查", "导出与说明"])
with plot_tab:
    for key, figure in charts.items():
        st.plotly_chart(figure, width="stretch", key=f"chart_{key}", config={"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2}})
    st.caption("折线连接采样点，不进行重采样或平滑。速率曲线不能直接用于计算 CO₂ 净埋存量。")
with data_tab:
    if data.warnings:
        for message in data.warnings:
            st.warning(message)
    else:
        st.success("已检查所选列：数值有限、无缺失、累计时间非负且唯一。")
    st.markdown("#### 整理后的数据")
    st.dataframe(frame, width="stretch", hide_index=True)
    st.caption("输出列名为标准字段；速率单位在导出的 JSON 元数据及 HTML 报告中记录。")
    with st.expander("查看源数据与字段对应"):
        st.dataframe(parsed.frame.head(100), width="stretch", hide_index=True)
        st.json(asdict(mapping))

metadata = {
    "application": "ReservoirViz", "version": __version__,
    "source_file": source_name, "source_sha256": hashlib.sha256(payload).hexdigest(),
    "synthetic_demo": is_demo,
    "data_provenance": "built-in synthetic example" if is_demo else "user-supplied CSV; provenance not independently verified",
    "rows": len(frame), "mapping": asdict(mapping),
    "parser": {**parsing, "detected_encoding": parsed.encoding, "detected_delimiter": parsed.delimiter},
    "output_units": {"time_days": "day", **({"pressure_mpa": "MPa"} if pressure_col else {}), **({"injection_rate": injection_unit} if injection_col else {}), **({"production_rate": production_unit} if production_col else {})},
    "warnings": data.warnings,
    "notes": ["Single-well / single-case time series.", "Rate values are not converted or subtracted.", "Sm³ reference conditions are defined by the source software, not by this app.", "No reservoir simulation or CO2 storage calculation is performed."],
}
with export_tab:
    st.markdown("#### 保存本次分析")
    st.write("HTML 报告包含交互图表和字段、单位说明，可离线打开。CSV 与 JSON 建议一起保存。")
    c1, c2, c3 = st.columns(3)
    c1.download_button("下载 HTML 报告", html_report(charts, metadata), "reservoirviz_report.html", "text/html", width="stretch", key="download_report")
    c2.download_button("下载整理后 CSV", frame.to_csv(index=False).encode("utf-8-sig"), "reservoirviz_normalized.csv", "text/csv", width="stretch", key="download_normalized")
    c3.download_button("下载单位与来源 JSON", json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"), "reservoirviz_metadata.json", "application/json", width="stretch", key="download_metadata")
    st.divider()
    st.markdown("**首版适用范围**：具有唯一累计时间的单井或单案例 CSV。压力支持 MPa / kPa / bar / psi；速率保留所选单位。")
    st.markdown("**数据处理**：应用不主动把上传内容写入磁盘，也不调用外部 AI/API。本机运行时数据由本机处理；如果将应用部署到服务器，上传内容会传至该服务器。")
    st.markdown("**数据限制**：CSV 可能包含需要跳过的说明行。当前不解析 SR3、网格或日历日期，也不计算累计注采、采收率或 CO₂ 埋存率。")
    st.caption("源软件设置、组分定义、压力基准及标准体积参考条件，均需由使用者按原始案例核对。")

st.divider()
st.caption(f"ReservoirViz {__version__} · Open-source time-series visualization · MIT License")
