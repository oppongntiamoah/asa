<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../lib/api.js";

  let rows = $state([]);
  let error = $state("");
  let loading = $state(true);
  let query = $state("");
  let sort = $state("market_value");
  let dir = $state("desc");

  const money = (v) => (v === null || v === undefined ? "—" : `GHS ${Number(v).toLocaleString("en-GH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
  const pct = (v) => (v === null || v === undefined ? "—" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`);

  async function load() {
    loading = true;
    error = "";
    try {
      rows = await api.holdings({ q: query, sort, dir });
    } catch (err) {
      error = err.message || "Couldn't load your holdings.";
    } finally {
      loading = false;
    }
  }

  function sortBy(field) {
    if (sort === field) {
      dir = dir === "desc" ? "asc" : "desc";
    } else {
      sort = field;
      dir = "desc";
    }
    load();
  }

  let searchTimeout;
  function onSearchInput() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(load, 300);
  }

  onMount(load);
</script>

<h1 class="text-xl font-semibold mb-6">Holdings</h1>

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
  <p class="text-gray-500">No holdings match.</p>
{:else}
  <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
          <th class="px-4 py-3 font-medium">Instrument</th>
          <th class="px-4 py-3 font-medium cursor-pointer" onclick={() => sortBy("quantity")}>Qty</th>
          <th class="px-4 py-3 font-medium cursor-pointer" onclick={() => sortBy("avg_cost")}>Avg cost</th>
          <th class="px-4 py-3 font-medium cursor-pointer" onclick={() => sortBy("current_price")}>Price</th>
          <th class="px-4 py-3 font-medium cursor-pointer" onclick={() => sortBy("market_value")}>Value</th>
          <th class="px-4 py-3 font-medium cursor-pointer" onclick={() => sortBy("gain_loss")}>Gain/loss</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as r}
          <tr
            class="border-b border-gray-100 dark:border-gray-800 last:border-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50"
            onclick={() => push(`/ticker/${r.instrument.ticker}`)}
          >
            <td class="px-4 py-3">
              <p class="font-medium text-emerald-700 dark:text-emerald-400">{r.instrument.ticker}</p>
              <p class="text-gray-500 text-xs">{r.instrument.name}</p>
            </td>
            <td class="px-4 py-3">{r.quantity.toLocaleString()}</td>
            <td class="px-4 py-3">{money(r.avg_cost)}</td>
            <td class="px-4 py-3">{money(r.current_price)}</td>
            <td class="px-4 py-3">{money(r.market_value)}</td>
            <td class="px-4 py-3 {r.gain_loss >= 0 ? 'text-emerald-600' : 'text-red-600'}">
              {money(r.gain_loss)} ({pct(r.pct_change)})
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
