<script>
  import { onMount } from "svelte";
  import { api } from "../../lib/api.js";
  import { money, pctColor } from "../../lib/format.js";

  let rows = $state([]);
  let loading = $state(true);
  let error = $state("");

  onMount(async () => {
    try {
      rows = await api.analysisTax();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<h1 class="text-xl font-semibold mb-2">Tax Summary</h1>
<p class="text-sm text-gray-500 mb-6">Realized gains by calendar year — not tax advice, use for your own filing reference.</p>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if rows.length === 0}
  <p class="text-gray-500">No realized gains yet.</p>
{:else}
  <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
          <th class="px-4 py-3 font-medium">Year</th>
          <th class="px-4 py-3 font-medium">Realized gain/(loss)</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as r}
          <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0">
            <td class="px-4 py-3">{r.year}</td>
            <td class="px-4 py-3 {pctColor(r.realized_gain)}">{money(r.realized_gain)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
