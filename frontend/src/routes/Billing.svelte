<script>
  import { onMount } from "svelte";
  import { api, ApiError } from "../lib/api.js";

  let plans = $state([]);
  let billingEnabled = $state(false);
  let loading = $state(true);
  let error = $state("");
  let purchasingCode = $state(null);

  onMount(async () => {
    try {
      const data = await api.billingPlans();
      plans = data.plans;
      billingEnabled = data.billing_enabled;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });

  async function purchase(code) {
    purchasingCode = code;
    error = "";
    try {
      const { authorization_url } = await api.startPurchase(code);
      window.location.href = authorization_url;
    } catch (err) {
      error = err instanceof ApiError ? err.message : "Couldn't start checkout.";
      purchasingCode = null;
    }
  }
</script>

<h1 class="text-xl font-semibold mb-2">Pricing</h1>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else}
  {#if !billingEnabled}
    <p class="text-sm text-emerald-700 bg-emerald-50 dark:bg-emerald-950 dark:text-emerald-300 rounded-lg px-4 py-3 mb-6">
      Everything is free right now — no credits are being charged.
    </p>
  {/if}
  {#if error}
    <p class="text-sm text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-3 py-2 mb-4">{error}</p>
  {/if}

  <div class="grid md:grid-cols-3 gap-6">
    {#each plans as plan}
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 flex flex-col">
        <p class="font-semibold mb-1">{plan.name}</p>
        <p class="text-2xl font-bold mb-4">GHS {plan.price_ghs}</p>
        <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-2 mb-6 flex-1">
          <li>{plan.pdf_processing_credits} PDF statement uploads</li>
          {#if plan.data_export_credits > 0}<li>{plan.data_export_credits} data exports</li>{/if}
          {#each plan.feature_bullets as bullet}
            <li>{bullet}</li>
          {/each}
        </ul>
        <button
          onclick={() => purchase(plan.code)}
          disabled={!billingEnabled || purchasingCode === plan.code}
          class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700 disabled:opacity-60"
        >
          {billingEnabled ? (purchasingCode === plan.code ? "Redirecting…" : "Buy") : "Included free"}
        </button>
      </div>
    {/each}
  </div>
{/if}
