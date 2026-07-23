<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api, ApiError } from "../lib/api.js";
  import { money, pct, pctColor } from "../lib/format.js";

  let rows = $state([]);
  let loading = $state(true);
  let error = $state("");
  let ticker = $state("");
  let addError = $state("");
  let adding = $state(false);

  async function load() {
    loading = true;
    try {
      rows = await api.watchlist();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  async function add(event) {
    event.preventDefault();
    addError = "";
    adding = true;
    try {
      await api.addWatchlist(ticker);
      ticker = "";
      await load();
    } catch (err) {
      addError = err instanceof ApiError ? err.message : "Couldn't add that ticker.";
    } finally {
      adding = false;
    }
  }

  async function remove(id) {
    try {
      await api.removeWatchlist(id);
      rows = rows.filter((r) => r.id !== id);
    } catch (err) {
      error = err.message;
    }
  }

  onMount(load);
</script>

<h1 class="text-xl font-semibold mb-6">Watchlist</h1>

<form onsubmit={add} class="flex gap-2 mb-6">
  <input
    type="text"
    placeholder="Ticker, e.g. MTNGH"
    bind:value={ticker}
    required
    class="rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
  />
  <button type="submit" disabled={adding} class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700 disabled:opacity-60">
    {adding ? "Adding…" : "Add"}
  </button>
</form>
{#if addError}
  <p class="text-sm text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-3 py-2 mb-4">{addError}</p>
{/if}

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if rows.length === 0}
  <p class="text-gray-500">Your watchlist is empty.</p>
{:else}
  <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
          <th class="px-4 py-3 font-medium">Instrument</th>
          <th class="px-4 py-3 font-medium">Price</th>
          <th class="px-4 py-3 font-medium">Change</th>
          <th class="px-4 py-3 font-medium">52w range</th>
          <th class="px-4 py-3 font-medium"></th>
        </tr>
      </thead>
      <tbody>
        {#each rows as r}
          <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0">
            <td class="px-4 py-3 font-medium text-emerald-700 dark:text-emerald-400 cursor-pointer hover:underline" onclick={() => push(`/ticker/${r.instrument.ticker}`)}>
              {r.instrument.ticker}
            </td>
            <td class="px-4 py-3">{money(r.current_price)}</td>
            <td class="px-4 py-3 {pctColor(r.change_pct)}">{pct(r.change_pct)}</td>
            <td class="px-4 py-3 text-gray-500">{money(r.low_52w)} – {money(r.high_52w)}</td>
            <td class="px-4 py-3 text-right">
              <button onclick={() => remove(r.id)} class="text-red-600 hover:underline text-xs">Remove</button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
