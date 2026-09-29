"""HTML and PDF report generation from dataset profile + charts."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.__version__ import __version__
from app.models.schemas import ChartRequest
from app.services.chart_service import ChartService
from app.services.profiling_service import ProfilingService


class ReportService:
    @staticmethod
    def generate_html(dataset_id: str, dataset_name: str) -> str:
        profile = ProfilingService.compute_profile(dataset_id)
        chart_section = ""
        numeric_cols = [c for c in profile.columns if c.inferred_type == "numeric"]
        text_cols = [c for c in profile.columns if c.inferred_type in ("categorical", "text")]

        if text_cols and numeric_cols:
            try:
                chart = ChartService.build_chart(
                    dataset_id,
                    ChartRequest(
                        chart_type="bar",
                        x_column=text_cols[0],
                        y_column=numeric_cols[0],
                        aggregation="sum",
                        limit=12,
                    ),
                )
                rows = "".join(
                    f"<tr><td>{html.escape(p.label)}</td><td>{p.value:,.2f}</td></tr>"
                    for p in chart.data[:12]
                )
                chart_section = f"""
                <h2>Chart — {html.escape(text_cols[0])} vs {html.escape(numeric_cols[0])}</h2>
                <table><thead><tr><th>Category</th><th>Value</th></tr></thead><tbody>{rows}</tbody></table>
                """
            except Exception:
                chart_section = "<p><em>Chart could not be generated for this dataset.</em></p>"

        col_rows = ""
        for c in profile.columns:
            col_rows += f"""
            <tr>
              <td>{html.escape(c.column)}</td>
              <td>{html.escape(c.inferred_type)}</td>
              <td>{c.null_percent}%</td>
              <td>{c.unique_count}</td>
              <td>{c.outlier_count}</td>
            </tr>"""

        insight_items = "".join(f"<li>{html.escape(i)}</li>" for i in profile.insights)
        corr_rows = ""
        for cr in profile.correlations[:15]:
            corr_rows += f"<tr><td>{html.escape(cr.column_a)}</td><td>{html.escape(cr.column_b)}</td><td>{cr.correlation}</td></tr>"

        generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>DataForge Report — {html.escape(dataset_name)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #171717; background: #fff; }}
    h1 {{ font-size: 1.75rem; }} h2 {{ margin-top: 2rem; border-bottom: 1px solid #e5e5e5; padding-bottom: 0.5rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.875rem; }}
    th, td {{ border: 1px solid #e5e5e5; padding: 0.5rem 0.75rem; text-align: left; }}
    th {{ background: #f5f5f5; }}
    .meta {{ color: #525252; font-size: 0.875rem; }}
    .kpis {{ display: flex; gap: 1.5rem; flex-wrap: wrap; margin: 1.5rem 0; }}
    .kpi {{ background: #f5f5f5; padding: 1rem 1.25rem; border-radius: 8px; min-width: 120px; }}
    .kpi strong {{ display: block; font-size: 1.5rem; }}
  </style>
</head>
<body>
  <h1>DataForge Analytics Report</h1>
  <p class="meta">Dataset: <strong>{html.escape(dataset_name)}</strong> · Generated {generated} · v{__version__}</p>
  <div class="kpis">
    <div class="kpi"><strong>{profile.row_count:,}</strong>Rows</div>
    <div class="kpi"><strong>{profile.column_count}</strong>Columns</div>
    <div class="kpi"><strong>{profile.duplicate_rows:,}</strong>Duplicates</div>
  </div>
  <h2>Insights</h2>
  <ul>{insight_items or "<li>No issues detected.</li>"}</ul>
  <h2>Column profile</h2>
  <table>
    <thead><tr><th>Column</th><th>Type</th><th>Missing %</th><th>Unique</th><th>Outliers</th></tr></thead>
    <tbody>{col_rows}</tbody>
  </table>
  <h2>Numeric correlations</h2>
  <table>
    <thead><tr><th>Column A</th><th>Column B</th><th>r</th></tr></thead>
    <tbody>{corr_rows or "<tr><td colspan='3'>Not enough numeric columns</td></tr>"}</tbody>
  </table>
  {chart_section}
  <p class="meta">Generated locally by DataForge Analytics — your data never left this machine.</p>
</body>
</html>"""

    @staticmethod
    def generate_pdf(dataset_id: str, dataset_name: str) -> bytes:
        profile = ProfilingService.compute_profile(dataset_id)
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48)
        styles = getSampleStyleSheet()
        story = [
            Paragraph(f"DataForge Report: {html.escape(dataset_name)}", styles["Title"]),
            Spacer(1, 12),
            Paragraph(
                f"Rows: {profile.row_count:,} · Columns: {profile.column_count} · "
                f"Duplicates: {profile.duplicate_rows:,}",
                styles["Normal"],
            ),
            Spacer(1, 16),
            Paragraph("Insights", styles["Heading2"]),
        ]
        for ins in profile.insights:
            story.append(Paragraph(f"• {html.escape(ins)}", styles["Normal"]))

        story.append(Spacer(1, 12))
        story.append(Paragraph("Column summary", styles["Heading2"]))
        table_data = [["Column", "Type", "Missing %", "Unique", "Outliers"]]
        for c in profile.columns:
            table_data.append(
                [c.column, c.inferred_type, f"{c.null_percent}", str(c.unique_count), str(c.outlier_count)]
            )
        t = Table(table_data, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f5")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(t)
        doc.build(story)
        return buf.getvalue()
