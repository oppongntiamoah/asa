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
            ? { bg: "transparent", text: "#9a9a9a", grid: "#262626", border: "#3a3a3a" }
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

        var chart = LightweightCharts.createChart(container, {
            layout: { background: { color: colors.bg }, textColor: colors.text },
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

        return api;
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
