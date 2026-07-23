<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../lib/api.js";
  import Money from "../lib/Money.svelte";

  let data = $state(null);
  let error = $state("");
  let loading = $state(true);

  const money = (v) => `GHS ${Number(v).toLocaleString("en-GH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const pct = (v) => (v === null || v === undefined ? "—" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`);

  onMount(async () => {
    try {
      data = await api.dashboard();
    } catch (err) {
      error = err.message || "Couldn't load your dashboard.";
    } finally {
      loading = false;
    }
  });
</script>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if !data.has_any_transactions}
  <div class="text-center py-16">
    <h1 class="text-xl font-semibold mb-2">Welcome to SikaTrack</h1>
    <p class="text-gray-500 mb-6">You haven't added any transactions yet.</p>
    <a href="/transactions/add/" class="inline-block bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700">
      Add your first transaction
    </a>
  </div>
{:else}
  <h1 class="text-xl font-semibold mb-6">Dashboard</h1>

  {#if data.has_stale_price}
    <p class="text-sm text-amber-800 bg-amber-50 dark:bg-amber-950 dark:text-amber-300 rounded-lg px-4 py-2 mb-6">
      Some prices are stale. Values shown use the most recent available close price.
    </p>
  {/if}

  <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Total value</p>
      <p class="text-lg font-semibold"><Money value={data.total_value} /></p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Today's change</p>
      <p class="text-lg font-semibold {data.todays_change.amount >= 0 ? 'text-emerald-600' : 'text-red-600'}">
        <Money value={data.todays_change.amount} /> ({pct(data.todays_change.pct)})
      </p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Unrealized P&L</p>
      <p class="text-lg font-semibold {data.total_unrealized_pnl >= 0 ? 'text-emerald-600' : 'text-red-600'}">
        <Money value={data.total_unrealized_pnl} /> ({pct(data.total_unrealized_pct)})
      </p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Cash balance</p>
      <p class="text-lg font-semibold"><Money value={data.cash_balance} /></p>
    </div>
  </div>

  {#if data.chart_svg}
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 mb-8 privacy-blur-chart">
      <p class="text-sm font-medium mb-3">Portfolio value over time</p>
      {@html data.chart_svg}
    </div>
  {/if}

  <div class="grid md:grid-cols-2 gap-4 mb-8">
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-sm font-medium mb-3">Top gainers</p>
      {#each data.movers.gainers as m}
        <div class="flex items-center justify-between py-1.5 text-sm">
          <button onclick={() => push(`/ticker/${m.instrument.ticker}`)} class="font-medium text-emerald-700 dark:text-emerald-400 hover:underline">{m.instrument.ticker}</button>
          <span class="text-emerald-600">{pct(m.change_pct)}</span>
        </div>
      {:else}
        <p class="text-sm text-gray-500">No data yet.</p>
      {/each}
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-sm font-medium mb-3">Top losers</p>
      {#each data.movers.losers as m}
        <div class="flex items-center justify-between py-1.5 text-sm">
          <button onclick={() => push(`/ticker/${m.instrument.ticker}`)} class="font-medium text-emerald-700 dark:text-emerald-400 hover:underline">{m.instrument.ticker}</button>
          <span class="text-red-600">{pct(m.change_pct)}</span>
        </div>
      {:else}
        <p class="text-sm text-gray-500">No data yet.</p>
      {/each}
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-sm font-medium mb-3">Most active by volume</p>
      {#each data.movers.volume_leaders as m}
        <div class="flex items-center justify-between py-1.5 text-sm">
          <button onclick={() => push(`/ticker/${m.instrument.ticker}`)} class="font-medium text-emerald-700 dark:text-emerald-400 hover:underline">{m.instrument.ticker}</button>
          <span class="text-gray-500">{m.volume.toLocaleString()}</span>
        </div>
      {:else}
        <p class="text-sm text-gray-500">No data yet.</p>
      {/each}
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-sm font-medium mb-3">Most active by value traded</p>
      {#each data.movers.value_leaders as m}
        <div class="flex items-center justify-between py-1.5 text-sm">
          <button onclick={() => push(`/ticker/${m.instrument.ticker}`)} class="font-medium text-emerald-700 dark:text-emerald-400 hover:underline">{m.instrument.ticker}</button>
          <span class="text-gray-500">{money(m.turnover_value)}</span>
        </div>
      {:else}
        <p class="text-sm text-gray-500">No data yet.</p>
      {/each}
    </div>
  </div>

  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
    <p class="text-sm font-medium mb-3">Allocation by sector</p>
    {#each data.sector_allocation as s}
      <div class="flex items-center justify-between py-1.5 text-sm">
        <span>{s.sector}</span>
        <span class="text-gray-500"><Money value={s.value} /> · {s.pct.toFixed(1)}%</span>
      </div>
    {/each}
  </div>
{/if}
