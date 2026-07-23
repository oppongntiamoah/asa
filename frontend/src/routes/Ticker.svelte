<script>
  import { onMount } from "svelte";
  import { pop } from "svelte-spa-router";
  import { api } from "../lib/api.js";
  import PriceChart from "../lib/PriceChart.svelte";

  let { params } = $props();

  let data = $state(null);
  let error = $state("");
  let loading = $state(true);

  const money = (v) => (v === null || v === undefined ? "—" : `GHS ${Number(v).toFixed(2)}`);
  const pct = (v) => (v === null || v === undefined ? "—" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`);

  async function load() {
    loading = true;
    error = "";
    try {
      data = await api.ticker(params.ticker);
    } catch (err) {
      error = err.message || "Couldn't load this ticker.";
    } finally {
      loading = false;
    }
  }

  onMount(load);
</script>

<button onclick={() => pop()} class="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-4 inline-flex items-center gap-1">
  <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
    <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
  </svg>
  Back
</button>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else}
  <div class="flex items-start justify-between mb-6 flex-wrap gap-4">
    <div>
      <div class="flex items-center gap-2 mb-1">
        <h1 class="text-xl font-semibold">{data.instrument.ticker}</h1>
        <span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500">{data.instrument.asset_class}</span>
      </div>
      <p class="text-gray-500">{data.instrument.name}{#if data.instrument.sector} · {data.instrument.sector}{/if}</p>
    </div>
    <div class="text-right">
      <p class="text-2xl font-semibold">{money(data.latest_price)}</p>
      <p class="text-sm {data.change_pct >= 0 ? 'text-emerald-600' : 'text-red-600'}">
        {pct(data.change_pct)} · as of {data.latest_trade_date ?? "—"}
      </p>
    </div>
  </div>

  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 mb-6">
    <PriceChart history={data.history} />
  </div>

  <p class="text-xs text-gray-400">
    Daily closing prices from GSE's published data, not live/real-time quotes.
  </p>
{/if}
