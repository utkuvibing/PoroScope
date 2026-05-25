"""HTML report generation for PoroScope batch results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def generate_html_report(
    summary_path: str | Path,
    output_path: str | Path | None = None,
    title: str = "PoroScope Batch Report",
) -> str:
    """Generate a self-contained HTML report from batch summary JSON.

    Parameters
    ----------
    summary_path : str | Path
        Path to batch_summary.json produced by run_batch.
    output_path : str | Path, optional
        If provided, write HTML to this path.
    title : str
        Report title.

    Returns
    -------
    str
        The generated HTML content.
    """
    import json

    with open(summary_path) as f:
        data = json.load(f)

    config = data.get("config", {})
    processed = data.get("processed_images", [])
    failed = data.get("failed_files", [])
    image_dir = data.get("image_dir", "")

    # Build stats
    n_total = data.get("processed_count", 0)
    n_failed = data.get("failed_count", 0)
    n_skipped = data.get("skipped_count", 0)

    if processed:
        porosities = [p["porosity_percent"] for p in processed if p.get("porosity_percent") is not None]
        pore_counts = [p["pore_count"] for p in processed if p.get("pore_count") is not None]
        avg_porosity = sum(porosities) / len(porosities) if porosities else 0
        total_pores = sum(pore_counts) if pore_counts else 0
        max_porosity = max(porosities) if porosities else 0
        min_porosity = min(porosities) if porosities else 0
    else:
        avg_porosity = total_pores = max_porosity = min_porosity = 0

    # Build config string
    config_str = (
        f"Pixel size: {config.get('pixel_size', '?')} {config.get('unit', '?')} | "
        f"Threshold: {config.get('threshold', '?')} | "
        f"Pores: {config.get('pores', '?')} | "
        f"Min size: {config.get('min_size', '?')} px"
    )

    # Image rows
    image_rows = ""
    for p in processed:
        overlay_path = ""
        if p.get("output_folder"):
            name = Path(p["output_folder"]).name
            overlay_path = str(Path(p["output_folder"]) / f"{name}_overlay.png")
        porosity = p.get("porosity_percent", "N/A")
        if porosity is not None:
            porosity = f"{porosity:.2f}%"
        pore_count = p.get("pore_count", "N/A")
        mean_area = p.get("mean_pore_area_unit2", "N/A")
        if mean_area is not None and isinstance(mean_area, (int, float)):
            mean_area = f"{mean_area:.1f}"

        image_rows += f"""
        <tr>
            <td>{p.get('image_name', '?')}</td>
            <td>{porosity}</td>
            <td>{pore_count}</td>
            <td>{mean_area}</td>
            <td><a href="{overlay_path}" target="_blank">View</a></td>
        </tr>"""

    # Failed rows
    failed_rows = ""
    for f_item in failed:
        failed_rows += f"""
        <tr>
            <td>{Path(f_item.get('image_path', '?')).name}</td>
            <td class="error">{f_item.get('error', '?')}</td>
        </tr>"""

    extra_sections = ""
    if not failed_rows:
        extra_sections += '<p class="success">✓ No errors</p>'
    else:
        extra_sections += f"""
        <h2>Failed Images ({n_failed})</h2>
        <table>
            <tr><th>Image</th><th>Error</th></tr>
            {failed_rows}
        </table>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 960px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #e0e0e0; }}
        h1, h2 {{ color: #89c4f4; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 20px 0; }}
        .stat-card {{ background: #16213e; border-radius: 8px; padding: 16px; text-align: center; border: 1px solid #333; }}
        .stat-value {{ font-size: 1.8em; font-weight: bold; color: #4fc3f7; }}
        .stat-label {{ font-size: 0.8em; color: #999; margin-top: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background: #16213e; color: #89c4f4; }}
        tr:hover {{ background: #1a1a3e; }}
        .error {{ color: #ef5350; }}
        .success {{ color: #66bb6a; }}
        .config {{ background: #16213e; border-radius: 8px; padding: 12px; margin: 16px 0; font-family: monospace; font-size: 0.9em; }}
        a {{ color: #4fc3f7; }}
        .footer {{ margin-top: 40px; font-size: 0.8em; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Source: <code>{image_dir}</code></p>

    <div class="config">⚙ {config_str}</div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{n_total}</div>
            <div class="stat-label">Images Processed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{avg_porosity:.1f}%</div>
            <div class="stat-label">Average Porosity</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_pores}</div>
            <div class="stat-label">Total Pores</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{min_porosity:.1f}%</div>
            <div class="stat-label">Min Porosity</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{max_porosity:.1f}%</div>
            <div class="stat-label">Max Porosity</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{n_failed}</div>
            <div class="stat-label">Failed</div>
        </div>
    </div>

    <h2>Results</h2>
    <table>
        <tr>
            <th>Image</th>
            <th>Porosity</th>
            <th>Pores</th>
            <th>Mean Area</th>
            <th>Overlay</th>
        </tr>
        {image_rows}
    </table>

    {extra_sections}

    <div class="footer">
        Generated by PoroScope v{data.get('poroscope_version', '?')} | {data.get('processed_count', 0) + data.get('failed_count', 0) + data.get('skipped_count', 0)} total files
    </div>
</body>
</html>"""

    if output_path:
        Path(output_path).write_text(html)

    return html