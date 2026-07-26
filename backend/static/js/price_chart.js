/*
 * Thin wrapper around TradingView's Lightweight Charts (vendored at
 * static/vendor/lightweight-charts.js — MIT-friendly Apache-2.0, no CDN,
 * no API key) for the interactive price/candle/volume chart used on the
 * per-ticker and holding-detail pages. Gives real zoom/pan/crosshair for
 * free instead of the static SVG fallback, which stays in the page's
 * initial HTML (see chart_svg in the view) so something renders even if
 * this script fails to load.
 *
 * Chart type toggle and the "save as image" button are deliberately
 * plain DOM/vanilla JS, not Alpine — this widget needs to work even if
 * Alpine hasn't initialized yet, and keeping it self-contained avoids any
 * ordering dependency between the two.
 */
(function () {
    function isDark() {
        return document.documentElement.classList.contains("dark");
    }

    function chartColors() {
        return isDark()
            ? { bg: "transparent", text: "#868da3", grid: "#1c1f2a", border: "#333a4b" }
            : { bg: "transparent", text: "#6b7280", grid: "#f3f4f6", border: "#e5e7eb" };
    }

    function initPriceChart(containerId, dataElementId, opts) {
        opts = opts || {};
        var container = document.getElementById(containerId);
        var dataEl = document.getElementById(dataElementId);
        if (!container || !dataEl || typeof LightweightCharts === "undefined") {
            return null;
        }

        var data = JSON.parse(dataEl.textContent);
        if (!data.line || !data.line.length) return null;
        var colors = chartColors();

        container.innerHTML = ""; // drop the static SVG fallback now that JS has taken over
        container.style.position = "relative";

        var chart = LightweightCharts.createChart(container, {
            layout: { background: { color: colors.bg }, textColor: colors.text, attributionLogo: false },
            grid: {
                vertLines: { color: colors.grid },
                horzLines: { color: colors.grid },
            },
            rightPriceScale: { borderColor: colors.border },
            timeScale: { borderColor: colors.border, timeVisible: false },
            autoSize: true,
            crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        });

        var lineSeries = chart.addSeries(LightweightCharts.LineSeries, {
            color: "#059669", lineWidth: 2, visible: true,
        });
        lineSeries.setData(data.line);

        var candleSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {
            upColor: "#059669", downColor: "#dc2626", borderVisible: false,
            wickUpColor: "#059669", wickDownColor: "#dc2626", visible: false,
        });
        candleSeries.setData(data.candles);

        if (data.volume && data.volume.length) {
            var volumeSeries = chart.addSeries(LightweightCharts.HistogramSeries, {
                priceFormat: { type: "volume" },
                priceScaleId: "volume",
            });
            volumeSeries.priceScale().applyOptions({
                scaleMargins: { top: 0.85, bottom: 0 },
            });
            volumeSeries.setData(data.volume);
        }

        chart.timeScale().fitContent();

        var api = { chart: chart, lineSeries: lineSeries, candleSeries: candleSeries };
        container._lwChart = api;

        var lineBtn = opts.lineButton ? document.getElementById(opts.lineButton) : null;
        var candleBtn = opts.candleButton ? document.getElementById(opts.candleButton) : null;
        var activeClasses = ["bg-emerald-600", "text-white"];
        var inactiveClasses = ["bg-white", "text-gray-500"];

        function setType(type) {
            var showCandle = type === "candle";
            lineSeries.applyOptions({ visible: !showCandle });
            candleSeries.applyOptions({ visible: showCandle });
            [lineBtn, candleBtn].forEach(function (btn) {
                if (!btn) return;
                btn.classList.remove.apply(btn.classList, activeClasses.concat(inactiveClasses));
            });
            if (lineBtn) lineBtn.classList.add.apply(lineBtn.classList, showCandle ? inactiveClasses : activeClasses);
            if (candleBtn) candleBtn.classList.add.apply(candleBtn.classList, showCandle ? activeClasses : inactiveClasses);
        }

        if (lineBtn) lineBtn.addEventListener("click", function () { setType("line"); });
        if (candleBtn) candleBtn.addEventListener("click", function () { setType("candle"); });

        setupDrawing(container, chart, lineSeries, candleSeries, opts);
        setupMaximize(container, chart, opts);

        return api;
    }

    /*
     * Lightweight Charts (the free/open-source library) has no built-in
     * drawing tools — those are a paid-tier "Charting Library" feature.
     * This is a from-scratch trend-line tool: a transparent <canvas>
     * overlaid on the chart, drawn on with plain mouse/touch events, with
     * each line stored as (time, price) pairs (not raw pixels) and
     * re-projected to pixel coordinates on every redraw — so lines stay
     * anchored to the right point on the chart as you pan/zoom/resize
     * instead of drifting.
     */
    function setupDrawing(container, chart, lineSeries, candleSeries, opts) {
        var drawBtn = opts.drawButton ? document.getElementById(opts.drawButton) : null;
        var clearBtn = opts.clearDrawButton ? document.getElementById(opts.clearDrawButton) : null;
        if (!drawBtn && !clearBtn) return;

        var overlay = document.createElement("canvas");
        overlay.style.position = "absolute";
        overlay.style.top = "0";
        overlay.style.left = "0";
        overlay.style.width = "100%";
        overlay.style.height = "100%";
        overlay.style.zIndex = "5";
        overlay.style.pointerEvents = "none";
        overlay.style.cursor = "crosshair";
        container.appendChild(overlay);

        var lines = []; // [{time1, price1, time2, price2}, ...]
        var drawing = false;
        var pending = null; // {time1, price1} while a line is being dragged out
        var active = function () { return candleSeries.options().visible ? candleSeries : lineSeries; };

        function resizeOverlay() {
            var ratio = window.devicePixelRatio || 1;
            overlay.width = container.clientWidth * ratio;
            overlay.height = container.clientHeight * ratio;
            overlay.getContext("2d").setTransform(ratio, 0, 0, ratio, 0, 0);
            redraw();
        }

        function toXY(time, price) {
            var x = chart.timeScale().timeToCoordinate(time);
            var y = active().priceToCoordinate(price);
            return { x: x, y: y };
        }

        function redraw() {
            var ctx = overlay.getContext("2d");
            ctx.clearRect(0, 0, container.clientWidth, container.clientHeight);
            ctx.strokeStyle = "#f59e0b";
            ctx.lineWidth = 1.5;
            lines.forEach(function (l) {
                var p1 = toXY(l.time1, l.price1);
                var p2 = toXY(l.time2, l.price2);
                if (p1.x === null || p2.x === null || p1.y === null || p2.y === null) return;
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            });
        }

        function pointFromEvent(evt) {
            var rect = container.getBoundingClientRect();
            var clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
            var clientY = evt.touches ? evt.touches[0].clientY : evt.clientY;
            return { x: clientX - rect.left, y: clientY - rect.top };
        }

        function toTimePrice(pt) {
            var time = chart.timeScale().coordinateToTime(pt.x);
            var price = active().coordinateToPrice(pt.y);
            return { time: time, price: price };
        }

        function onStart(evt) {
            if (!drawing) return;
            evt.preventDefault();
            var tp = toTimePrice(pointFromEvent(evt));
            if (tp.time === null || tp.price === null) return;
            pending = { time1: tp.time, price1: tp.price };
        }

        function onMove(evt) {
            if (!drawing || !pending) return;
            evt.preventDefault();
            var tp = toTimePrice(pointFromEvent(evt));
            if (tp.time === null || tp.price === null) return;
            redraw();
            var ctx = overlay.getContext("2d");
            var p1 = toXY(pending.time1, pending.price1);
            var p2 = toXY(tp.time, tp.price);
            ctx.strokeStyle = "#f59e0b";
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        }

        function onEnd(evt) {
            if (!drawing || !pending) return;
            var tp = toTimePrice(pointFromEvent(evt.changedTouches ? evt.changedTouches[0] : evt));
            if (tp.time !== null && tp.price !== null) {
                lines.push({ time1: pending.time1, price1: pending.price1, time2: tp.time, price2: tp.price });
            }
            pending = null;
            redraw();
        }

        overlay.addEventListener("mousedown", onStart);
        overlay.addEventListener("mousemove", onMove);
        window.addEventListener("mouseup", onEnd);
        overlay.addEventListener("touchstart", onStart, { passive: false });
        overlay.addEventListener("touchmove", onMove, { passive: false });
        overlay.addEventListener("touchend", onEnd);

        chart.timeScale().subscribeVisibleTimeRangeChange(redraw);
        new ResizeObserver(resizeOverlay).observe(container);
        resizeOverlay();

        function setDrawing(on) {
            drawing = on;
            overlay.style.pointerEvents = on ? "auto" : "none";
            if (drawBtn) {
                drawBtn.classList.toggle("bg-amber-500", on);
                drawBtn.classList.toggle("text-white", on);
                drawBtn.classList.toggle("bg-white", !on);
                drawBtn.classList.toggle("text-gray-500", !on);
            }
        }

        if (drawBtn) drawBtn.addEventListener("click", function () { setDrawing(!drawing); });
        if (clearBtn) clearBtn.addEventListener("click", function () { lines = []; redraw(); });

        container._lwDrawing = { redraw: redraw, resizeOverlay: resizeOverlay };
    }

    /*
     * "Maximize" is a CSS-only fullscreen (fixed overlay covering the
     * viewport), not the browser Fullscreen API — more reliable across
     * mobile browsers, which restrict requestFullscreen() on arbitrary
     * elements. The chart's own `autoSize: true` picks up the container's
     * new dimensions via its internal ResizeObserver, so no manual
     * chart.resize() call is needed — just resize the container.
     *
     * Applied via inline styles rather than Tailwind utility classes: a
     * statically-built Tailwind bundle only emits CSS for class names it
     * finds in template source, so classes only ever added at runtime
     * (like this fullscreen toggle) can silently have no effect depending
     * on how Tailwind is wired up. Inline styles always work.
     */
    function setupMaximize(container, chart, opts) {
        var btn = opts.maximizeButton ? document.getElementById(opts.maximizeButton) : null;
        var wrapper = opts.wrapperId ? document.getElementById(opts.wrapperId) : null;
        if (!btn || !wrapper) return;

        var normalHeight = container.style.height || "320px";
        var savedWrapperStyle = wrapper.getAttribute("style") || "";
        var maximized = false;

        function apply() {
            if (maximized) {
                wrapper.style.position = "fixed";
                wrapper.style.top = "0";
                wrapper.style.left = "0";
                wrapper.style.right = "0";
                wrapper.style.bottom = "0";
                wrapper.style.zIndex = "9999";
                wrapper.style.overflow = "auto";
                wrapper.style.borderRadius = "0";
                wrapper.style.background = isDark() ? "#111827" : "#ffffff";
                container.style.height = "calc(100vh - 140px)";
                btn.textContent = "✕ Close";
            } else {
                wrapper.setAttribute("style", savedWrapperStyle);
                container.style.height = normalHeight;
                btn.textContent = "⤢ Maximize";
            }
            if (container._lwDrawing) container._lwDrawing.resizeOverlay();
        }

        btn.addEventListener("click", function () {
            maximized = !maximized;
            apply();
        });

        document.addEventListener("keydown", function (evt) {
            if (evt.key === "Escape" && maximized) {
                maximized = false;
                apply();
            }
        });
    }

    /*
     * Screenshots the chart via Lightweight Charts' own takeScreenshot()
     * (a real HTMLCanvasElement, not a DOM-scraping approximation), stamps
     * a SikaTrack watermark in the corner, and triggers a PNG download.
     */
    function exportChartAsImage(containerId, filename) {
        var container = document.getElementById(containerId);
        if (!container || !container._lwChart) return;

        var source = container._lwChart.chart.takeScreenshot();
        var canvas = document.createElement("canvas");
        canvas.width = source.width;
        canvas.height = source.height;
        var ctx = canvas.getContext("2d");
        ctx.drawImage(source, 0, 0);

        var pad = Math.max(12, Math.round(source.width * 0.012));
        var boxH = Math.max(28, Math.round(source.width * 0.032));
        var logoSize = boxH - 10;
        var label = "SikaTrack";
        ctx.font = "600 " + Math.round(boxH * 0.42) + "px system-ui, -apple-system, sans-serif";
        var textWidth = ctx.measureText(label).width;
        var boxW = logoSize + 10 + textWidth + 20;
        var x = source.width - boxW - pad;
        var y = source.height - boxH - pad;

        ctx.fillStyle = "rgba(20, 20, 20, 0.72)";
        ctx.beginPath();
        ctx.roundRect(x, y, boxW, boxH, boxH / 2);
        ctx.fill();

        ctx.fillStyle = "#059669";
        ctx.beginPath();
        ctx.roundRect(x + 5, y + 5, logoSize, logoSize, 6);
        ctx.fill();
        ctx.fillStyle = "#ffffff";
        ctx.font = "700 " + Math.round(logoSize * 0.62) + "px system-ui, -apple-system, sans-serif";
        ctx.textBaseline = "middle";
        ctx.textAlign = "center";
        ctx.fillText("S", x + 5 + logoSize / 2, y + 5 + logoSize / 2 + 1);

        ctx.fillStyle = "#ffffff";
        ctx.font = "600 " + Math.round(boxH * 0.42) + "px system-ui, -apple-system, sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(label, x + logoSize + 15, y + boxH / 2 + 1);

        canvas.toBlob(function (blob) {
            var url = URL.createObjectURL(blob);
            var a = document.createElement("a");
            a.href = url;
            a.download = (filename || "sikatrack-chart") + ".png";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    window.SikaTrackCharts = window.SikaTrackCharts || {};
    window.SikaTrackCharts.initPriceChart = initPriceChart;
    window.SikaTrackCharts.exportChartAsImage = exportChartAsImage;
})();
