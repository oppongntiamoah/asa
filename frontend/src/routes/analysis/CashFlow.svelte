<script>
  import { onMount } from "svelte";
  import { api } from "../../lib/api.js";
  import { pctColor } from "../../lib/format.js";
  import Money from "../../lib/Money.svelte";

  let rows = $state([]);
  let loading = $state(true);
  let error = $state("");

  onMount(async () => {
    try {
      rows = await api.analysisCashFlow();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<h1 class="text-xl font-semibold mb-2">Cash Flow</h1>
<p class="text-sm text-gray-500 mb-6">Money moving into/out of positions by month — not a full brokerage cash ledger.</p>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if rows.length === 0}
  <p class="text-gray-500">No activity yet.</p>
{:else}
  <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
          <th class="px-4 py-3 font-medium">Month</th>
          <th class="px-4 py-3 font-medium">Invested</th>
          <th class="px-4 py-3 font-medium">Divested</th>
          <th class="px-4 py-3 font-medium">Net</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as r}
          <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0">
            <td class="px-4 py-3">{r.month}</td>
            <td class="px-4 py-3"><Money value={r.invested} /></td>
            <td class="px-4 py-3"><Money value={r.divested} /></td>
            <td class="px-4 py-3 {pctColor(r.net)}"><Money value={r.net} /></td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
