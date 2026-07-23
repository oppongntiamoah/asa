"""
Minimal server-rendered SVG line chart — deliberately not a JS charting
library (Chart.js etc.), per the low-bandwidth/no-heavy-JS design
constraint. Good enough for a single portfolio-value line; not meant to
grow into a general charting library.
"""


def svg_line_chart(series, width=600, height=180, stroke="#059669", fill="#05966922"):
    """series: [(label, float_value), ...]. Returns an inline <svg> string,
    or None if there isn't enough data to draw a line."""
    if len(series) < 2:
        return None

    values = [v for _, v in series]
    min_v, max_v = min(values), max(values)
    value_range = (max_v - min_v) or 1
    n = len(series)
    padding = 8

    def x_at(i):
        return padding + (i / (n - 1)) * (width - 2 * padding)

    def y_at(v):
        return height - padding - ((v - min_v) / value_range) * (height - 2 * padding)

    points = [(x_at(i), y_at(v)) for i, (_, v) in enumerate(series)]
    line_path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(points))
    area_path = line_path + f" L{points[-1][0]:.1f},{height - padding} L{points[0][0]:.1f},{height - padding} Z"

    return (
        f'<svg viewBox="0 0 {width} {height}" class="w-full h-auto" preserveAspectRatio="none">'
        f'<path d="{area_path}" fill="{fill}" stroke="none"></path>'
        f'<path d="{line_path}" fill="none" stroke="{stroke}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"></path>'
        f"</svg>"
    )
