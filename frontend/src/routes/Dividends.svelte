<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../lib/api.js";
  import { pct } from "../lib/format.js";
  import Money from "../lib/Money.svelte";

  let data = $state(null);
  let loading = $state(true);
  let error = $state("");

  onMount(async () => {
    try {
      data = await api.dividends();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<h1 class="text-xl font-semibold mb-6">Dividends</h1>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else}
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Total received</p>
      <p class="text-lg font-semibold"><Money value={data.total_received} /></p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">This year</p>
      <p class="text-lg font-semibold"><Money value={data.this_year} /></p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Portfolio yield (TTM)</p>
      <p class="text-lg font-semibold">{pct(data.portfolio_yield_pct)}</p>
    </div>
  </div>

  {#if data.upcoming.length > 0}
    <h2 class="text-sm font-medium mb-3">Upcoming</h2>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 mb-8">
      {#each data.upcoming as u}
        <div class="flex items-center justify-between py-1.5 text-sm">
          <button onclick={() => push(`/ticker/${u.instrument.ticker}`)} class="font-medium text-emerald-700 dark:text-emerald-400 hover:underline">{u.instrument.ticker}</button>
          <span class="text-gray-500">GHS {u.amount_per_share}/share · ex {u.ex_dividend_date}</span>
        </div>
      {/each}
    </div>
  {/if}

  {#if data.per_holding_yield.length > 0}
    <h2 class="text-sm font-medium mb-3">Yield by holding (TTM)</h2>
    <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl mb-8">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
            <th class="px-4 py-3 font-medium">Instrument</th>
            <th class="px-4 py-3 font-medium">Received (TTM)</th>
            <th class="px-4 py-3 font-medium">Yield</th>
          </tr>
        </thead>
        <tbody>
          {#each data.per_holding_yield as h}
            <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0">
              <td class="px-4 py-3 font-medium">{h.instrument.ticker}</td>
              <td class="px-4 py-3"><Money value={h.trailing_12mo_received} /></td>
              <td class="px-4 py-3">{pct(h.yield_pct)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}

  {#if data.receipts.length > 0}
    <h2 class="text-sm font-medium mb-3">All receipts</h2>
    <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
            <th class="px-4 py-3 font-medium">Instrument</th>
            <th class="px-4 py-3 font-medium">Ex-date</th>
            <th class="px-4 py-3 font-medium">Qty held</th>
            <th class="px-4 py-3 font-medium">Amount</th>
          </tr>
        </thead>
        <tbody>
          {#each data.receipts as r}
            <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0">
              <td class="px-4 py-3 font-medium">{r.instrument.ticker}</td>
              <td class="px-4 py-3">{r.ex_dividend_date}</td>
              <td class="px-4 py-3 money-mask">{r.quantity_held}</td>
              <td class="px-4 py-3"><Money value={r.total_amount} /></td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <p class="text-gray-500">No dividends received yet.</p>
  {/if}
{/if}
