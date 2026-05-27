from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.engine import HistoryResult, MonteCarloResult, WindowResult
from src.rules import ChallengeConfig, evaluate_window

_STATUS_FILL = {
    "PASS": "rgba(0,200,100,0.15)",
    "FAIL_MAX_DD": "rgba(220,50,50,0.15)",
    "FAIL_DAILY_DD": "rgba(255,140,0,0.15)",
    "FAIL_TIME": "rgba(120,120,120,0.15)",
}

_STATUS_SOLID = {
    "PASS": "rgba(0,200,100,0.85)",
    "FAIL_MAX_DD": "rgba(220,50,50,0.85)",
    "FAIL_DAILY_DD": "rgba(255,140,0,0.85)",
    "FAIL_TIME": "rgba(120,120,120,0.85)",
}

_CURVE_PASS = "rgba(0,200,100,0.3)"
_CURVE_FAIL = "rgba(220,50,50,0.3)"


def _write_html(figs: list[go.Figure], out_path: str) -> None:
    divs = "\n".join(f.to_html(full_html=False, include_plotlyjs=False) for f in figs)
    html = (
        "<!DOCTYPE html><html>"
        "<head><meta charset='utf-8'>"
        "<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>"
        "<style>body{background:#111;margin:0;padding:16px;font-family:sans-serif;}</style>"
        "</head>"
        f"<body>{divs}</body></html>"
    )
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)


def _merge_window_groups(
    windows: list[WindowResult],
) -> list[tuple[WindowResult, WindowResult, str, list[WindowResult]]]:
    groups: list[tuple[WindowResult, WindowResult, str, list[WindowResult]]] = []
    i = 0
    while i < len(windows):
        status = windows[i].result.status
        j = i + 1
        while j < len(windows) and windows[j].result.status == status:
            j += 1
        groups.append((windows[i], windows[j - 1], status, windows[i:j]))
        i = j
    return groups


def render_montecarlo(
    result: MonteCarloResult,
    config: ChallengeConfig,
    out_path: str,
) -> None:
    target_equity = config.account_size * (1 + config.profit_target_pct / 100)

    fig1 = go.Figure()
    seen_pass = False
    seen_fail = False

    for curve in result.sampled_curves:
        sim = evaluate_window(curve, config)
        is_pass = sim.status == "PASS"
        color = _CURVE_PASS if is_pass else _CURVE_FAIL
        name = "Pass" if is_pass else "Fail"
        show = (is_pass and not seen_pass) or (not is_pass and not seen_fail)
        if is_pass:
            seen_pass = True
        else:
            seen_fail = True
        fig1.add_trace(
            go.Scatter(
                x=list(curve.index),
                y=list(curve.values),
                mode="lines",
                line=dict(color=color, width=1),
                name=name,
                legendgroup=name,
                showlegend=show,
                hoverinfo="skip",
            )
        )

    fig1.add_hline(
        y=target_equity,
        line_dash="dash",
        line_color="rgba(0,220,110,0.8)",
        annotation_text=f"Target +{config.profit_target_pct}%",
        annotation_position="top right",
    )
    fig1.add_hline(
        y=config.account_size,
        line_dash="dot",
        line_color="rgba(180,180,180,0.5)",
        annotation_text="Start",
        annotation_position="bottom right",
    )
    fig1.update_layout(
        template="plotly_dark",
        title=f"Monte Carlo Sampled Equity Curves — {config.name}  "
              f"({len(result.sampled_curves)} of {len(result.all_results)} shown)",
        xaxis_title="Trading Day",
        yaxis_title="Equity",
        legend=dict(x=0.01, y=0.99),
        height=400,
    )

    final_equities = [r.final_equity for r in result.all_results]
    fig2 = go.Figure()
    fig2.add_trace(
        go.Histogram(
            x=final_equities,
            nbinsx=80,
            marker_color="rgba(100,160,255,0.7)",
            name="Final Equity",
            hovertemplate="Equity: %{x:,.0f}<br>Count: %{y}<extra></extra>",
        )
    )
    fig2.add_vline(
        x=target_equity,
        line_dash="dash",
        line_color="rgba(0,220,110,0.9)",
        annotation_text=f"Target {config.profit_target_pct}%",
        annotation_position="top right",
    )
    fig2.add_vline(
        x=config.account_size,
        line_dash="dot",
        line_color="rgba(180,180,180,0.5)",
        annotation_text="Start",
        annotation_position="top left",
    )
    fig2.update_layout(
        template="plotly_dark",
        title=f"Final Equity Distribution — Pass rate: {result.pass_rate:.1f}%  "
              f"| Avg days (pass): {result.avg_days_pass:.1f}  "
              f"| Avg days (fail): {result.avg_days_fail:.1f}",
        xaxis_title="Final Equity",
        yaxis_title="Count",
        height=350,
    )

    statuses = list(result.failure_breakdown.keys())
    pcts = list(result.failure_breakdown.values())
    bar_colors = [_STATUS_SOLID.get(s, "rgba(150,150,150,0.8)") for s in statuses]

    fig3 = go.Figure()
    fig3.add_trace(
        go.Bar(
            x=pcts,
            y=statuses,
            orientation="h",
            marker_color=bar_colors,
            text=[f"{p:.1f}%" for p in pcts],
            textposition="inside",
            hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
        )
    )
    fig3.update_layout(
        template="plotly_dark",
        title="Outcome Breakdown",
        xaxis_title="% of Runs",
        yaxis_title="",
        xaxis=dict(range=[0, max(100, max(pcts) * 1.05)]),
        height=280,
    )

    _write_html([fig1, fig2, fig3], out_path)


def render_history(
    result: HistoryResult,
    config: ChallengeConfig,
    out_path: str,
) -> None:
    equity_df = result.equity_df
    fig = go.Figure()

    if result.windows:
        y_min = float(equity_df["equity"].min())
        y_max = float(equity_df["equity"].max())
        y_pad = (y_max - y_min) * 0.06
        y_lo = y_min - y_pad
        y_hi = y_max + y_pad

        dates_arr = equity_df["date"]
        date_step = (
            (dates_arr.iloc[1] - dates_arr.iloc[0])
            if len(dates_arr) > 1
            else pd.Timedelta(days=1)
        )

        for first_w, last_w, status, group in _merge_window_groups(result.windows):
            x0 = first_w.start_date
            x1 = last_w.start_date + date_step

            worst_dd = min(w.result.max_dd_pct for w in group)
            worst_daily = min(w.result.max_daily_dd_pct for w in group)
            last_equity = last_w.result.final_equity
            n_windows = len(group)
            hover = (
                f"<b>{status}</b><br>"
                f"Start: {x0.strftime('%Y-%m-%d')}<br>"
                f"End: {last_w.end_date.strftime('%Y-%m-%d')}<br>"
                f"Windows: {n_windows}<br>"
                f"Worst Max DD: {worst_dd:.2f}%<br>"
                f"Worst Daily DD: {worst_daily:.2f}%<br>"
                f"Final Equity: {last_equity:,.2f}"
                "<extra></extra>"
            )

            fig.add_vrect(
                x0=x0,
                x1=x1,
                fillcolor=_STATUS_FILL[status],
                layer="below",
                line_width=0,
            )

            fig.add_trace(
                go.Scatter(
                    x=[x0, x0, x1, x1, x0],
                    y=[y_lo, y_hi, y_hi, y_lo, y_lo],
                    fill="toself",
                    fillcolor="rgba(0,0,0,0)",
                    line=dict(width=0),
                    mode="lines",
                    hovertemplate=hover,
                    hoveron="fills",
                    showlegend=False,
                    name="",
                )
            )

    fig.add_trace(
        go.Scatter(
            x=equity_df["date"],
            y=equity_df["equity"],
            mode="lines",
            line=dict(color="rgba(220,220,220,0.9)", width=1.5),
            name="Equity",
            hovertemplate="Date: %{x|%Y-%m-%d}<br>Equity: %{y:,.2f}<extra></extra>",
        )
    )

    for status, fill_color in _STATUS_FILL.items():
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(size=12, color=_STATUS_SOLID[status], symbol="square"),
                name=status,
                showlegend=True,
            )
        )

    fig.update_layout(
        template="plotly_dark",
        title=f"Historical Window Analysis — {config.name}  "
              f"({len(result.windows)} windows, {config.max_trading_days}-day challenge)",
        xaxis_title="Date",
        yaxis_title="Equity",
        hovermode="closest",
        legend=dict(x=0.01, y=0.99),
        height=550,
    )

    _write_html([fig], out_path)
