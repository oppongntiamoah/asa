<script>
  import { onMount } from "svelte";
  import { api } from "../../lib/api.js";
  import { pct, pctColor } from "../../lib/format.js";

  let data = $state(null);
  let loading = $state(true);
  let error = $state("");

  const fmtPct = (v) => (v === null || v === undefined ? "Not enough history yet" : `${v.toFixed(2)}%`);

  function corrColor(v) {
    if (v === null || v === undefined) return "";
    const abs = Math.abs(v);
    if (abs > 0.7) return v > 0 ? "bg-emerald-100 dark:bg-emerald-950" : "bg-red-100 dark:bg-red-950";
    if (abs > 0.3) return v > 0 ? "bg-emerald-50 dark:bg-emerald-950/50" : "bg-red-50 dark:bg-red-950/50";
    return "";
  }

  onMount(async () => {
    try {
      data = await api.analysisPerformance();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<h1 class="text-xl font-semibold mb-6">Performance</h1>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if !data.has_series}
  <p class="text-gray-500">Not enough price history yet to compute performance metrics.</p>
{:else}
  {#if data.chart_svg}
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 mb-8">
      <p class="text-sm font-medium mb-3">Portfolio value ({data.history_days} days of history)</p>
      {@html data.chart_svg}
    </div>
  {/if}

  <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">CAGR</p>
      <p class="text-lg font-semibold">{data.cagr === null ? "—" : fmtPct(data.cagr)}</p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">XIRR</p>
      <p class="text-lg font-semibold">{data.xirr === null ? "—" : fmtPct(data.xirr)}</p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Volatility (annualized)</p>
      <p class="text-lg font-semibold">{data.volatility === null ? "—" : fmtPct(data.volatility)}</p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Value at Risk (95%, daily)</p>
      <p class="text-lg font-semibold">{data.var_95 === null ? "—" : fmtPct(data.var_95)}</p>
    </div>
    {#if data.max_drawdown}
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
        <p class="text-xs text-gray-500 mb-1">Max drawdown</p>
        <p class="text-lg font-semibold text-red-600">{data.max_drawdown.max_drawdown_pct.toFixed(2)}%</p>
        <p class="text-xs text-gray-400">{data.max_drawdown.peak_date} → {data.max_drawdown.trough_date}</p>
      </div>
    {/if}
  </div>

  {#if data.rolling_30d.length > 0}
    <h2 class="text-sm font-medium mb-3">30-day rolling return</h2>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 mb-8">
      {#each data.rolling_30d as r}
        <div class="flex items-center justify-between py-1.5 text-sm">
          <span>{r.date}</span>
          <span class={pctColor(r.return_pct)}>{pct(r.return_pct)}</span>
        </div>
      {/each}
    </div>
  {/if}

  {#if data.correlation_grid}
    <h2 class="text-sm font-medium mb-3">Holdings correlation</h2>
    <p class="text-xs text-gray-400 mb-3">Based on daily returns — noisy for thinly-traded stocks, treat as directional only.</p>
    <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
      <table class="text-sm">
        <thead>
          <tr>
            <th class="px-3 py-2"></th>
            {#each data.correlation_tickers as t}
              <th class="px-3 py-2 font-medium text-gray-500">{t}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each data.correlation_grid as row}
            <tr>
              <td class="px-3 py-2 font-medium text-gray-500">{row.ticker}</td>
              {#each row.cells as cell}
                <td class="px-3 py-2 text-center {corrColor(cell)}">{cell === null || cell === undefined ? "—" : cell.toFixed(2)}</td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
{/if}
