"""
Server-rendered SVG charts for the low-bandwidth default case (portfolio
value on the dashboard, a quick sparkline), plus lightweight_chart_data()
below which feeds TradingView's Lightweight Charts (vendored at
static/vendor/lightweight-charts.js) for the interactive zoom/pan price
charts on the per-ticker and holding-detail pages. The SVG functions
still matter as the no-JS fallback baked into the initial HTML.
"""
import math


def svg_donut_chart(segments, size=160, thickness=20):
    """segments: [{"pct": float 0-100, "color": "#hex or hsl(...)"}, ...].
    Draws each segment as a stroked arc on a shared circle (stroke-dasharray
    trick) rather than pie wedges — simpler math, no path-arc edge cases at
    0%/100%. Returns None if nothing to show."""
    segments = [s for s in segments if s.get("pct", 0) > 0]
    if not segments:
        return None

    radius = (size - thickness) / 2
    circumference = 2 * math.pi * radius
    cx = cy = size / 2
    offset = 0.0
    arcs = []
    for s in segments:
        dash = (s["pct"] / 100) * circumference
        gap = max(circumference - dash, 0)
        arcs.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius:.2f}" fill="none" stroke="{s["color"]}" '
            f'stroke-width="{thickness}" stroke-dasharray="{dash:.2f} {gap:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})" '
            f'stroke-linecap="butt"></circle>'
        )
        offset += dash

    return f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}">' + "".join(arcs) + "</svg>"


def svg_ring_gauge(value, max_value=100, size=88, thickness=9, color="#ffffff", track_color="rgba(255,255,255,0.25)"):
    """A single-value progress ring (health score out of 100, etc.) with
    the number in the center. value/max_value clamped to [0, 1]."""
    if value is None:
        return None
    frac = max(0.0, min(1.0, value / max_value)) if max_value else 0.0
    radius = (size - thickness) / 2
    circumference = 2 * math.pi * radius
    dash = frac * circumference
    gap = circumference - dash
    cx = cy = size / 2
    font_size = size * 0.28
    return (
        f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
        f'<circle cx="{cx}" cy="{cy}" r="{radius:.2f}" fill="none" stroke="{track_color}" stroke-width="{thickness}"></circle>'
        f'<circle cx="{cx}" cy="{cy}" r="{radius:.2f}" fill="none" stroke="{color}" stroke-width="{thickness}" '
        f'stroke-dasharray="{dash:.2f} {gap:.2f}" stroke-linecap="round" '
        f'transform="rotate(-90 {cx} {cy})"></circle>'
        f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" '
        f'font-size="{font_size:.1f}" font-weight="700" fill="{color}">{value:g}</text>'
        f"</svg>"
    )


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


def svg_volume_chart(bars, width=600, height=48, color="#9ca3af33"):
    """bars: chronological PriceBar-like objects. One bar per day using
    `volume`; days without a volume figure are just skipped (not drawn as
    zero), since GSE's earliest ingested rows may predate that field.
    Returns None if no bar in the series carries a volume at all."""
    if not any(b.volume is not None for b in bars):
        return None

    max_v = max((b.volume for b in bars if b.volume is not None), default=0) or 1
    n = len(bars)
    padding = 2
    slot_width = (width - 2 * padding) / n
    bar_width = max(slot_width * 0.7, 1)

    parts = []
    for i, b in enumerate(bars):
        if b.volume is None:
            continue
        bar_height = max((b.volume / max_v) * (height - 2 * padding), 1)
        x = padding + slot_width * i + (slot_width - bar_width) / 2
        y = height - padding - bar_height
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" '
            f'height="{bar_height:.1f}" fill="{color}"></rect>'
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="w-full h-auto" preserveAspectRatio="none">'
        + "".join(parts)
        + "</svg>"
    )


def lightweight_chart_data(bars):
    """Serializes chronological PriceBar-like objects into the shape
    static/js/price_chart.js feeds to Lightweight Charts: a close-price
    line, an OHLC candle series, and a volume histogram.

    Same honesty rule as svg_candle_chart: a bar only gets a real high/low
    wick when both are actually present (see instruments/ingest/
    csv_ingest.py) — otherwise its candle body is derived from open/close
    alone, never a fabricated wick.
    """
    line, candles, volume = [], [], []
    for b in bars:
        if b.close_price is None:
            continue
        t = b.trade_date.isoformat()
        close = float(b.close_price)
        line.append({"time": t, "value": close})

        if b.open_price is not None:
            open_ = float(b.open_price)
            high = float(b.high_price) if b.high_price is not None else max(open_, close)
            low = float(b.low_price) if b.low_price is not None else min(open_, close)
            candles.append({"time": t, "open": open_, "high": high, "low": low, "close": close})

        if b.volume is not None:
            up = b.open_price is None or close >= float(b.open_price)
            volume.append({
                "time": t,
                "value": b.volume,
                "color": "#05966955" if up else "#dc262655",
            })

    return {"line": line, "candles": candles, "volume": volume}
