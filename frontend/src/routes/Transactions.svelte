<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../lib/api.js";
  import { money, num } from "../lib/format.js";

  let txns = $state([]);
  let loading = $state(true);
  let error = $state("");
  let deletingId = $state(null);

  async function load() {
    loading = true;
    try {
      txns = await api.transactions();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  async function remove(id) {
    if (!confirm("Remove this transaction? This will recalculate your holding.")) return;
    deletingId = id;
    try {
      await api.deleteTransaction(id);
      txns = txns.filter((t) => t.id !== id);
    } catch (err) {
      error = err.message;
    } finally {
      deletingId = null;
    }
  }

  onMount(load);
</script>

<div class="flex items-center justify-between mb-6">
  <h1 class="text-xl font-semibold">Transactions</h1>
  <button onclick={() => push("/transactions/add")} class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700">
    Add transaction
  </button>
</div>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if txns.length === 0}
  <p class="text-gray-500">No transactions yet.</p>
{:else}
  <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
          <th class="px-4 py-3 font-medium">Date</th>
          <th class="px-4 py-3 font-medium">Type</th>
          <th class="px-4 py-3 font-medium">Instrument</th>
          <th class="px-4 py-3 font-medium">Qty</th>
          <th class="px-4 py-3 font-medium">Price</th>
          <th class="px-4 py-3 font-medium">Fees</th>
          <th class="px-4 py-3 font-medium">Total</th>
          <th class="px-4 py-3 font-medium"></th>
        </tr>
      </thead>
      <tbody>
        {#each txns as t}
          <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0">
            <td class="px-4 py-3">{t.trade_date}</td>
            <td class="px-4 py-3">
              <span class="text-xs font-medium px-2 py-0.5 rounded-full {t.transaction_type === 'BUY' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300'}">
                {t.transaction_type}
              </span>
            </td>
            <td class="px-4 py-3 font-medium">{t.instrument.ticker}</td>
            <td class="px-4 py-3">{num(t.quantity)}</td>
            <td class="px-4 py-3">{money(t.price_per_share)}</td>
            <td class="px-4 py-3">{money(t.fees)}</td>
            <td class="px-4 py-3">{money(t.gross_amount)}</td>
            <td class="px-4 py-3 text-right whitespace-nowrap">
              <button onclick={() => push(`/transactions/${t.id}/edit`)} class="text-emerald-700 dark:text-emerald-400 hover:underline text-xs mr-3">Edit</button>
              <button onclick={() => remove(t.id)} disabled={deletingId === t.id} class="text-red-600 hover:underline text-xs disabled:opacity-50">
                {deletingId === t.id ? "…" : "Remove"}
              </button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
