<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../../lib/api.js";
  import { money, pct, pctColor } from "../../lib/format.js";
  import Money from "../../lib/Money.svelte";

  let rows = $state([]);
  let loading = $state(true);
  let error = $state("");

  onMount(async () => {
    try {
      rows = await api.costBasis();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<h1 class="text-xl font-semibold mb-6">Cost Basis</h1>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if rows.length === 0}
  <p class="text-gray-500">No holdings yet.</p>
{:else}
  <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
          <th class="px-4 py-3 font-medium">Instrument</th>
          <th class="px-4 py-3 font-medium">Avg cost</th>
          <th class="px-4 py-3 font-medium">Break-even</th>
          <th class="px-4 py-3 font-medium">Current price</th>
          <th class="px-4 py-3 font-medium">Gain/share</th>
          <th class="px-4 py-3 font-medium">Gain %</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as r}
          <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50" onclick={() => push(`/ticker/${r.instrument.ticker}`)}>
            <td class="px-4 py-3 font-medium text-emerald-700 dark:text-emerald-400">{r.instrument.ticker}</td>
            <td class="px-4 py-3"><Money value={r.average_cost} /></td>
            <td class="px-4 py-3"><Money value={r.break_even_price} /></td>
            <td class="px-4 py-3">{money(r.current_price)}</td>
            <td class="px-4 py-3 {pctColor(r.gain_per_share)}"><Money value={r.gain_per_share} /></td>
            <td class="px-4 py-3 {pctColor(r.gain_pct)}">{pct(r.gain_pct)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
