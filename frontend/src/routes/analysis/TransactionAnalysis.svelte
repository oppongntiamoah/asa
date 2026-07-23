<script>
  import { onMount } from "svelte";
  import { api } from "../../lib/api.js";
  import { money } from "../../lib/format.js";

  let data = $state(null);
  let loading = $state(true);
  let error = $state("");

  onMount(async () => {
    try {
      data = await api.analysisTransactions();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<h1 class="text-xl font-semibold mb-6">Transaction Analysis</h1>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else}
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Total buys</p>
      <p class="text-lg font-semibold">{data.total_buys}</p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Total sells</p>
      <p class="text-lg font-semibold">{data.total_sells}</p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Avg purchase price</p>
      <p class="text-lg font-semibold">{money(data.avg_purchase_price)}</p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Trades/month</p>
      <p class="text-lg font-semibold">{data.trading_frequency_per_month.toFixed(1)}</p>
    </div>
  </div>

  <div class="grid md:grid-cols-2 gap-4 mb-8">
    {#if data.largest_purchase}
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
        <p class="text-sm font-medium mb-2">Largest purchase</p>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          {data.largest_purchase.instrument.ticker} — {data.largest_purchase.quantity} @ {money(data.largest_purchase.price_per_share)}
          ({money(data.largest_purchase.gross_amount)}) on {data.largest_purchase.trade_date}
        </p>
      </div>
    {/if}
    {#if data.largest_sale}
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
        <p class="text-sm font-medium mb-2">Largest sale</p>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          {data.largest_sale.instrument.ticker} — {data.largest_sale.quantity} @ {money(data.largest_sale.price_per_share)}
          ({money(data.largest_sale.gross_amount)}) on {data.largest_sale.trade_date}
        </p>
      </div>
    {/if}
  </div>

  {#if data.avg_holding_period_days !== null}
    <p class="text-sm text-gray-600 dark:text-gray-400 mb-8">
      Average holding period: <strong>{Math.round(data.avg_holding_period_days)} days</strong>
    </p>
  {/if}

  <h2 class="text-sm font-medium mb-3">Monthly activity</h2>
  <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
          <th class="px-4 py-3 font-medium">Month</th>
          <th class="px-4 py-3 font-medium">Buys</th>
          <th class="px-4 py-3 font-medium">Sells</th>
          <th class="px-4 py-3 font-medium">Trades</th>
        </tr>
      </thead>
      <tbody>
        {#each data.monthly as m}
          <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0">
            <td class="px-4 py-3">{m.month}</td>
            <td class="px-4 py-3">{money(m.buys)}</td>
            <td class="px-4 py-3">{money(m.sells)}</td>
            <td class="px-4 py-3">{m.count}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
