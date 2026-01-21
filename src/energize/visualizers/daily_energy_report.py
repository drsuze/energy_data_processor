# visualize daily energy stats using tables and graphs e.g. heatmaps

import pandas as pd
import plotly.express as px
from pathlib import Path
import tempfile


def heatmap_daily_energy(
    energy_df: pd.DataFrame,
    plot_value: str,
):
    """Given daily energy stats, create heatmap of throughput amounts across the site."""

    energy_df["BESS container ID"] = (
        energy_df["Inverter ID"] + "-" + energy_df["BESS ID"].astype(str)
    )

    pivot_df = energy_df.pivot(
        index="date", columns="BESS container ID", values=plot_value
    )
    fig = px.imshow(
        pivot_df,
        color_continuous_scale="Viridis",  # Customize the color scale
        title=f"Heatmap of daily {plot_value} per BESS container",
    )
    fig.update_coloraxes(colorbar_title=plot_value)

    return fig


def build_html_report(
    table_gaps: pd.DataFrame,
    fig1,
    fig2,
    table1: pd.DataFrame,
    title: str = "Energy Results Report",
):
    """
    Builds a self-contained HTML report from 2 Plotly figures and 2 tables.
    """
    table_gaps_html = table_gaps.to_html(index=False, border=0)

    plot1_html = fig1.to_html(include_plotlyjs="cdn", full_html=False)
    plot2_html = fig2.to_html(include_plotlyjs=False, full_html=False)

    table1_html = table1.to_html(index=False, border=0)

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <title>{title}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                margin: 40px;
            }}
            h1 {{
                margin-bottom: 10px;
            }}
            h2 {{
                margin-top: 40px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border-bottom: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f5f5f5;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>

        <h2>Data Gaps (if any)</h2>
        {table_gaps_html}

        <h2>Discharged Energy (kWh)</h2>
        {plot1_html}

        <h2>Charged Energy (kWh)</h2>
        {plot2_html}

        <h2>BESS Throughput - Lowest 5 by Discharged Energy</h2>
        {table1_html}

    </body>
    </html>
    """
    return html


def write_report_and_csv(
    table_gaps,
    fig1,
    fig2,
    table1: pd.DataFrame,
    table2: pd.DataFrame,
):
    """
    Writes the HTML report and CSV for table2.
    Returns file paths for Gradio downloads.
    """
    tmp_dir = Path(tempfile.mkdtemp())

    html_path = tmp_dir / "energy_report.html"
    csv_path = tmp_dir / "BESS_throughput_all_days.csv"

    html = build_html_report(table_gaps, fig1, fig2, table1)
    html_path.write_text(html, encoding="utf-8")

    table2.to_csv(csv_path, index=False)

    return str(html_path), str(csv_path)
