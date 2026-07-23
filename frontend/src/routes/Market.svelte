<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../lib/api.js";
  import { money, pct, pctColor } from "../lib/format.js";

  let rows = $state([]);
  let latestDate = $state(null);
  let query = $state("");
  let loading = $state(true);
  let error = $state("");

  async function load() {
    loading = true;
    try {
      const data = await api.marketList(query);
      rows = data.rows;
      latestDate = data.latest_date;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  let searchTimeout;
  function onSearchInput() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(load, 300);
  }

  onMount(load);
</script>

<div class="flex items-center justify-between mb-2 flex-wrap gap-2">
  <h1 class="text-xl font-semibold">Market</h1>
  {#if latestDate}
    <span class="text-xs text-gray-400">Daily closes as of {latestDate} — not live quotes</span>
  {/if}
</div>

<input
  type="text"
  placeholder="Search ticker or name…"
  bind:value={query}
  oninput={onSearchInput}
  class="w-full max-w-xs mb-4 rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
/>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if rows.length === 0}
  <p class="text-gray-500">No instruments match.</p>
{:else}
  <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
          <th class="px-4 py-3 font-medium">Ticker</th>
          <th class="px-4 py-3 font-medium">Name</th>
          <th class="px-4 py-3 font-medium">Price</th>
          <th class="px-4 py-3 font-medium">Change</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as r}
          <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50" onclick={() => push(`/ticker/${r.instrument.ticker}`)}>
            <td class="px-4 py-3 font-medium text-emerald-700 dark:text-emerald-400">{r.instrument.ticker}</td>
            <td class="px-4 py-3 text-gray-500">{r.instrument.name}</td>
            <td class="px-4 py-3">{money(r.close_price)}</td>
            <td class="px-4 py-3 {pctColor(r.change_pct)}">{pct(r.change_pct)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
