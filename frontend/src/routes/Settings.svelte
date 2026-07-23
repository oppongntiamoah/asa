<script>
  import { onMount } from "svelte";
  import { api, ApiError } from "../lib/api.js";
  import { checkAuth } from "../lib/auth.js";

  let profile = $state({ username: "", first_name: "", last_name: "", email: "", phone_number: "" });
  let cashAmount = $state("0");
  let loading = $state(true);
  let error = $state("");
  let profileSaved = $state(false);
  let cashSaved = $state(false);
  let savingProfile = $state(false);
  let savingCash = $state(false);

  onMount(async () => {
    try {
      const [p, c] = await Promise.all([api.profile(), api.cashBalance()]);
      profile = p;
      cashAmount = String(c.amount_ghs);
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });

  async function saveProfile(event) {
    event.preventDefault();
    savingProfile = true;
    profileSaved = false;
    error = "";
    try {
      profile = await api.updateProfile(profile);
      await checkAuth();
      profileSaved = true;
    } catch (err) {
      error = err instanceof ApiError ? err.message : "Couldn't save profile.";
    } finally {
      savingProfile = false;
    }
  }

  async function saveCash(event) {
    event.preventDefault();
    savingCash = true;
    cashSaved = false;
    error = "";
    try {
      await api.updateCashBalance(cashAmount);
      cashSaved = true;
    } catch (err) {
      error = err instanceof ApiError ? err.message : "Couldn't save cash balance.";
    } finally {
      savingCash = false;
    }
  }
</script>

<h1 class="text-xl font-semibold mb-6">Settings</h1>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else}
  {#if error}
    <p class="text-sm text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-3 py-2 mb-4">{error}</p>
  {/if}

  <form onsubmit={saveProfile} class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 max-w-lg space-y-4 mb-6">
    <h2 class="text-sm font-semibold">Profile</h2>
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label for="first_name" class="block text-sm font-medium mb-1">First name</label>
        <input id="first_name" type="text" bind:value={profile.first_name} class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
      </div>
      <div>
        <label for="last_name" class="block text-sm font-medium mb-1">Last name</label>
        <input id="last_name" type="text" bind:value={profile.last_name} class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
      </div>
    </div>
    <div>
      <label for="email" class="block text-sm font-medium mb-1">Email</label>
      <input id="email" type="email" bind:value={profile.email} class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
    </div>
    <div>
      <label for="phone" class="block text-sm font-medium mb-1">Phone number</label>
      <input id="phone" type="text" bind:value={profile.phone_number} placeholder="0XX XXX XXXX" class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
    </div>
    <button type="submit" disabled={savingProfile} class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700 disabled:opacity-60">
      {savingProfile ? "Saving…" : "Save profile"}
    </button>
    {#if profileSaved}<span class="text-sm text-emerald-600 ml-3">Saved.</span>{/if}
  </form>

  <form onsubmit={saveCash} class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 max-w-lg space-y-4 mb-6">
    <h2 class="text-sm font-semibold">Cash balance</h2>
    <p class="text-xs text-gray-500">Manually set — SikaTrack doesn't track a cash ledger, just the current figure for your total portfolio value.</p>
    <div>
      <label for="cash" class="block text-sm font-medium mb-1">Amount (GHS)</label>
      <input id="cash" type="number" step="0.01" min="0" bind:value={cashAmount} class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
    </div>
    <button type="submit" disabled={savingCash} class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700 disabled:opacity-60">
      {savingCash ? "Saving…" : "Save cash balance"}
    </button>
    {#if cashSaved}<span class="text-sm text-emerald-600 ml-3">Saved.</span>{/if}
  </form>

  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 max-w-lg space-y-3">
    <h2 class="text-sm font-semibold">More</h2>
    <a href="/accounts/settings/export/" class="block text-sm text-emerald-700 dark:text-emerald-400 hover:underline">Export my transactions (CSV)</a>
    <a href="/accounts/password-change/" class="block text-sm text-emerald-700 dark:text-emerald-400 hover:underline">Change password</a>
    <a href="/accounts/settings/delete/" class="block text-sm text-red-600 hover:underline">Request account deletion</a>
  </div>
{/if}
