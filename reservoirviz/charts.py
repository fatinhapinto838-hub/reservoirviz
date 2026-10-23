"""Plotly charts and a self-contained offline HTML report."""

from __future__ import annotations

import html
import json

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .data import ValidatedData

COLORS = {"pressure_mpa": "#163d55", "injection_rate": "#0b8a80", "production_rate": "#e58042"}


def _style(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(
        title=title, template="plotly_white", height=400,
        margin=dict(l=35, r=25, t=60, b=45),
        font=dict(family="Arial, sans-serif", size=13, color="#183647"),
        hovermode="x unified", legend=dict(orientation="h", y=1.12, x=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    figure.update_xaxes(title_text="Time (day)", gridcolor="#edf1f4", zeroline=False)
    figure.update_yaxes(gridcolor="#edf1f4", zeroline=False)
    return figure


def make_charts(data: ValidatedData) -> dict[str, go.Figure]:
    frame, mapping = data.frame, data.mapping
    charts = {}
    if "pressure_mpa" in frame:
        figure = go.Figure(go.Scatter(x=frame.time_days, y=frame.pressure_mpa, name="Pressure", mode="lines", line=dict(color=COLORS["pressure_mpa"], width=2.5)))
        _style(figure, "Pressure history").update_yaxes(title_text="Pressure (MPa)")
        charts["pressure"] = figure
    signals = [(column, label, unit) for column, label, unit in [
        ("injection_rate", "Injection", mapping.injection_unit),
        ("production_rate", "Production", mapping.production_unit),
    ] if column in frame]
    if signals:
        split = len(signals) == 2 and signals[0][2] != signals[1][2]
        figure = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.18) if split else go.Figure()
        for index, (column, label, unit) in enumerate(signals):
            trace = go.Scatter(x=frame.time_days, y=frame[column], name=f"{label} ({unit})", mode="lines", line=dict(color=COLORS[column], width=2.5))
            if split:
                figure.add_trace(trace, row=index + 1, col=1)
                figure.update_yaxes(title_text=f"{label} ({unit})", row=index + 1, col=1)
            else:
                figure.add_trace(trace)
        _style(figure, "Injection & production rates")
        if split:
            figure.update_layout(height=550)
            figure.update_xaxes(title_text="", row=1, col=1)
        else:
            figure.update_yaxes(title_text=f"Rate ({signals[0][2]})")
        charts["rates"] = figure
    return charts


def html_report(charts: dict[str, go.Figure], metadata: dict) -> str:
    """Embed Plotly JS once, so the saved report works without a CDN."""
    sections = [figure.to_html(full_html=False, include_plotlyjs=index == 0) for index, figure in enumerate(charts.values())]
    details = html.escape(json.dumps(metadata, ensure_ascii=False, indent=2))
    return """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ReservoirViz report</title><style>body{max-width:1120px;margin:40px auto;padding:0 24px;font:16px/1.6 system-ui;color:#183647;background:#f6f8fa}section,pre{background:white;padding:20px;border-radius:12px}pre{overflow:auto;font-size:12px}h1{letter-spacing:-1px}.note{color:#526877}</style></head><body>
<h1>ReservoirViz · Analysis report</h1><p class="note">Exported time series visualization. Check source provenance and units in the metadata. This report does not calculate CO₂ storage or validate reservoir physics.</p>""" + "".join(f"<section>{section}</section>" for section in sections) + f"<h2>Data & units</h2><pre>{details}</pre></body></html>"
