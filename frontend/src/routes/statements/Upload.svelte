<script>
  import { push } from "svelte-spa-router";
  import { api, ApiError } from "../../lib/api.js";

  let broker = $state("IC_SECURITIES");
  let file = $state(null);
  let error = $state("");
  let submitting = $state(false);

  function onFileChange(event) {
    file = event.target.files[0] || null;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) {
      error = "Choose a PDF file.";
      return;
    }
    error = "";
    submitting = true;
    try {
      const formData = new FormData();
      formData.append("broker", broker);
      formData.append("file", file);
      const statement = await api.uploadStatement(formData);
      push(`/statements/${statement.id}`);
    } catch (err) {
      error = err instanceof ApiError ? err.message : "Upload failed.";
    } finally {
      submitting = false;
    }
  }
</script>

<h1 class="text-xl font-semibold mb-6">Upload statement</h1>

<form onsubmit={handleSubmit} class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 max-w-lg space-y-4">
  {#if error}
    <p class="text-sm text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-3 py-2">{error}</p>
  {/if}

  <div>
    <label for="broker" class="block text-sm font-medium mb-1">Broker</label>
    <select id="broker" bind:value={broker} class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm">
      <option value="IC_SECURITIES">IC Securities</option>
      <option value="BLACKSTAR">Black Star Advisors</option>
    </select>
  </div>

  <div>
    <label for="file" class="block text-sm font-medium mb-1">Statement PDF</label>
    <input id="file" type="file" accept=".pdf" onchange={onFileChange} required class="w-full text-sm" />
  </div>

  <p class="text-xs text-gray-500">
    We'll extract transactions automatically, then show you a review screen before anything is saved to your portfolio.
  </p>

  <div class="flex gap-3">
    <button type="submit" disabled={submitting} class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700 disabled:opacity-60">
      {submitting ? "Uploading…" : "Upload"}
    </button>
    <button type="button" onclick={() => push("/statements")} class="text-sm font-medium px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-900">
      Cancel
    </button>
  </div>
</form>
