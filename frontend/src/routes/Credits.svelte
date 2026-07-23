<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../lib/api.js";
  import { money } from "../lib/format.js";

  let data = $state(null);
  let loading = $state(true);
  let error = $state("");

  onMount(async () => {
    try {
      data = await api.billingCredits();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<h1 class="text-xl font-semibold mb-6">My Credits</h1>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else}
  {#if !data.billing_enabled}
    <p class="text-sm text-emerald-700 bg-emerald-50 dark:bg-emerald-950 dark:text-emerald-300 rounded-lg px-4 py-3 mb-6">
      Everything is free right now — credit balances aren't being enforced.
    </p>
  {/if}

  <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">PDF processing</p>
      <p class="text-lg font-semibold">{data.balance.pdf_processing_credits}</p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Data export</p>
      <p class="text-lg font-semibold">{data.balance.data_export_credits}</p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Stock alerts</p>
      <p class="text-lg font-semibold">{data.balance.stock_alert_credits}</p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Dividend alerts</p>
      <p class="text-lg font-semibold">{data.balance.dividend_alert_credits}</p>
    </div>
  </div>

  <div class="flex items-center justify-between mb-3">
    <h2 class="text-sm font-medium">Purchase history</h2>
    <button onclick={() => push("/billing")} class="text-sm text-emerald-700 dark:text-emerald-400 hover:underline">Buy more credits</button>
  </div>

  {#if data.purchases.length === 0}
    <p class="text-gray-500 text-sm">No purchases yet.</p>
  {:else}
    <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
            <th class="px-4 py-3 font-medium">Plan</th>
            <th class="px-4 py-3 font-medium">Amount</th>
            <th class="px-4 py-3 font-medium">Status</th>
            <th class="px-4 py-3 font-medium">Date</th>
          </tr>
        </thead>
        <tbody>
          {#each data.purchases as p}
            <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0">
              <td class="px-4 py-3">{p.plan_name}</td>
              <td class="px-4 py-3">{money(p.amount_ghs)}</td>
              <td class="px-4 py-3">{p.status}</td>
              <td class="px-4 py-3 text-gray-500">{new Date(p.created_at).toLocaleDateString()}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
{/if}
