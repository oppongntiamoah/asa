"""
Minimal server-rendered SVG charts — deliberately not a JS charting
library (Chart.js etc.), per the low-bandwidth/no-heavy-JS design
constraint. Good enough for a single portfolio-value line or a per-ticker
candlestick view; not meant to grow into a general charting library.
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


def svg_candle_chart(bars, width=600, height=180, up_color="#059669", down_color="#dc2626"):
    """bars: chronological iterable of PriceBar-like objects (open_price,
    close_price, and optionally high_price/low_price).

    GSE's daily CSV export only carries open/close, not intraday high/low
    (see instruments/ingest/csv_ingest.py), so we never invent a wick: a
    bar draws a true high/low wick only when both are present on it,
    otherwise just the open/close body.

    Returns (svg_str, has_intraday_range) — has_intraday_range is False
    when no bar in the series has real high/low data, so the caller can
    caption the chart honestly. Returns (None, False) if there isn't
    enough data to draw anything.
    """
    candles = [b for b in bars if b.open_price is not None and b.close_price is not None]
    if len(candles) < 2:
        return None, False

    has_range = any(b.high_price is not None and b.low_price is not None for b in candles)

    values = []
    for b in candles:
        o, c = float(b.open_price), float(b.close_price)
        h = float(b.high_price) if b.high_price is not None else max(o, c)
        l = float(b.low_price) if b.low_price is not None else min(o, c)
        values.extend([h, l])

    min_v, max_v = min(values), max(values)
    value_range = (max_v - min_v) or 1
    n = len(candles)
    padding = 8
    plot_width = width - 2 * padding
    slot_width = plot_width / n
    body_width = max(slot_width * 0.6, 1)

    def x_at(i):
        return padding + slot_width * (i + 0.5)

    def y_at(v):
        return height - padding - ((v - min_v) / value_range) * (height - 2 * padding)

    parts = []
    for i, b in enumerate(candles):
        o, c = float(b.open_price), float(b.close_price)
        color = up_color if c >= o else down_color
        cx = x_at(i)
        y_open, y_close = y_at(o), y_at(c)
        top, bottom = min(y_open, y_close), max(y_open, y_close)
        body_height = max(bottom - top, 1)

        if b.high_price is not None and b.low_price is not None:
            y_high, y_low = y_at(float(b.high_price)), y_at(float(b.low_price))
            parts.append(
                f'<line x1="{cx:.1f}" y1="{y_high:.1f}" x2="{cx:.1f}" y2="{y_low:.1f}" '
                f'stroke="{color}" stroke-width="1"></line>'
            )

        parts.append(
            f'<rect x="{cx - body_width / 2:.1f}" y="{top:.1f}" width="{body_width:.1f}" '
            f'height="{body_height:.1f}" fill="{color}"></rect>'
        )

    svg = (
        f'<svg viewBox="0 0 {width} {height}" class="w-full h-auto" preserveAspectRatio="none">'
        + "".join(parts)
        + "</svg>"
    )
    return svg, has_range
