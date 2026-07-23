<script>
  import { onMount } from "svelte";
  import { pop } from "svelte-spa-router";
  import { api } from "../lib/api.js";
  import PriceChart from "../lib/PriceChart.svelte";
  import { money, num, pct, pctColor } from "../lib/format.js";

  let { params } = $props();

  let data = $state(null);
  let error = $state("");
  let loading = $state(true);

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
      <p class="text-sm {pctColor(data.change_pct)}">
        {pct(data.change_pct)} · as of {data.latest_trade_date ?? "—"}
      </p>
    </div>
  </div>

  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 mb-6">
    <PriceChart history={data.history} />
  </div>

  <p class="text-xs text-gray-400 mb-6">
    Daily closing prices from GSE's published data, not live/real-time quotes.
  </p>

  {#if data.position}
    <h2 class="text-lg font-semibold mb-3">Your position</h2>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
        <p class="text-xs text-gray-500 mb-1">Quantity</p>
        <p class="text-lg font-semibold">{num(data.position.quantity)}</p>
      </div>
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
        <p class="text-xs text-gray-500 mb-1">Avg cost</p>
        <p class="text-lg font-semibold">{money(data.position.average_cost)}</p>
      </div>
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
        <p class="text-xs text-gray-500 mb-1">Market value</p>
        <p class="text-lg font-semibold">{money(data.position.market_value)}</p>
      </div>
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
        <p class="text-xs text-gray-500 mb-1">Unrealized P&L</p>
        <p class="text-lg font-semibold {pctColor(data.position.unrealized_pnl)}">
          {money(data.position.unrealized_pnl)} ({pct(data.position.unrealized_pnl_pct)})
        </p>
      </div>
    </div>

    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl overflow-x-auto mb-6">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
            <th class="px-4 py-3 font-medium">Date</th>
            <th class="px-4 py-3 font-medium">Type</th>
            <th class="px-4 py-3 font-medium">Qty</th>
            <th class="px-4 py-3 font-medium">Price</th>
            <th class="px-4 py-3 font-medium">Total</th>
          </tr>
        </thead>
        <tbody>
          {#each data.position.transactions as t}
            <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0">
              <td class="px-4 py-3">{t.trade_date}</td>
              <td class="px-4 py-3">{t.transaction_type}</td>
              <td class="px-4 py-3">{num(t.quantity)}</td>
              <td class="px-4 py-3">{money(t.price_per_share)}</td>
              <td class="px-4 py-3">{money(t.gross_amount)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    {#if data.position.dividend_receipts.length > 0}
      <h3 class="text-sm font-medium mb-3">Dividends received</h3>
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
        {#each data.position.dividend_receipts as d}
          <div class="flex items-center justify-between py-1.5 text-sm">
            <span>{d.ex_dividend_date} · GHS {d.amount_per_share}/share</span>
            <span class="text-gray-500">{money(d.total_amount)}</span>
          </div>
        {/each}
      </div>
    {/if}
  {/if}
{/if}
