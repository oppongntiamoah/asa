<script>
  // Lightweight dependency-free line chart. The data is daily closes from
  // GSE's published CSV, not live ticks, so there's no need for anything
  // more elaborate than SVG + a hover tooltip.
  let { history, height = 280 } = $props();

  const ranges = [
    { key: "1M", days: 21 },
    { key: "3M", days: 63 },
    { key: "6M", days: 126 },
    { key: "1Y", days: 252 },
    { key: "ALL", days: null },
  ];
  let activeRange = $state("ALL");

  let filtered = $derived.by(() => {
    const range = ranges.find((r) => r.key === activeRange);
    if (!range || range.days === null) return history;
    return history.slice(-range.days);
  });

  const width = 700;
  const padding = { top: 16, right: 16, bottom: 28, left: 56 };

  let points = $derived.by(() => {
    if (filtered.length === 0) return [];
    const values = filtered.map((h) => h.close_price);
    const minV = Math.min(...values);
    const maxV = Math.max(...values);
    const range = maxV - minV || 1;
    const innerW = width - padding.left - padding.right;
    const innerH = height - padding.top - padding.bottom;
    return filtered.map((h, i) => ({
      x: padding.left + (filtered.length === 1 ? 0 : (i / (filtered.length - 1)) * innerW),
      y: padding.top + innerH - ((h.close_price - minV) / range) * innerH,
      date: h.trade_date,
      price: h.close_price,
    }));
  });

  let linePath = $derived(points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" "));
  let areaPath = $derived(
    points.length
      ? `${linePath} L${points[points.length - 1].x.toFixed(1)},${height - padding.bottom} L${points[0].x.toFixed(1)},${height - padding.bottom} Z`
      : ""
  );

  let hoverIndex = $state(null);
  let hovered = $derived(hoverIndex !== null ? points[hoverIndex] : null);

  function onMove(event) {
    if (points.length === 0) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const relX = ((event.clientX - rect.left) / rect.width) * width;
    let nearest = 0;
    let nearestDist = Infinity;
    points.forEach((p, i) => {
      const dist = Math.abs(p.x - relX);
      if (dist < nearestDist) {
        nearestDist = dist;
        nearest = i;
      }
    });
    hoverIndex = nearest;
  }

  const isUp = $derived(filtered.length > 1 && filtered[filtered.length - 1].close_price >= filtered[0].close_price);
</script>

<div>
  <div class="flex gap-1 mb-3">
    {#each ranges as r}
      <button
        onclick={() => (activeRange = r.key)}
        class="text-xs font-medium px-2.5 py-1 rounded-md {activeRange === r.key
          ? 'bg-emerald-600 text-white'
          : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'}"
      >
        {r.key}
      </button>
    {/each}
  </div>

  {#if points.length < 2}
    <p class="text-sm text-gray-500 py-12 text-center">Not enough price history yet.</p>
  {:else}
    <svg
      viewBox="0 0 {width} {height}"
      class="w-full h-auto"
      onmousemove={onMove}
      onmouseleave={() => (hoverIndex = null)}
      role="img"
      aria-label="Price history chart"
    >
      <path d={areaPath} fill={isUp ? "#05966922" : "#dc262622"} stroke="none" />
      <path d={linePath} fill="none" stroke={isUp ? "#059669" : "#dc2626"} stroke-width="2" />
      {#if hovered}
        <line x1={hovered.x} y1={padding.top} x2={hovered.x} y2={height - padding.bottom} stroke="currentColor" stroke-opacity="0.15" />
        <circle cx={hovered.x} cy={hovered.y} r="3.5" fill={isUp ? "#059669" : "#dc2626"} />
      {/if}
    </svg>
    {#if hovered}
      <p class="text-sm text-gray-500 -mt-2">
        {hovered.date} · GHS {hovered.price.toFixed(2)}
      </p>
    {/if}
  {/if}
</div>
