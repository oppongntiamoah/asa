<script>
  import { push } from "svelte-spa-router";
  import { login, ApiError } from "../lib/auth.js";

  let username = $state("");
  let password = $state("");
  let error = $state("");
  let submitting = $state(false);

  async function handleSubmit(event) {
    event.preventDefault();
    error = "";
    submitting = true;
    try {
      await login(username, password);
      push("/");
    } catch (err) {
      error = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
    } finally {
      submitting = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center px-4">
  <div class="w-full max-w-sm">
    <div class="flex items-center gap-2 justify-center mb-8">
      <span class="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold">S</span>
      <span class="text-xl font-bold">SikaTrack</span>
    </div>

    <form onsubmit={handleSubmit} class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 space-y-4">
      <h1 class="text-lg font-semibold">Log in</h1>

      {#if error}
        <p class="text-sm text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-3 py-2">{error}</p>
      {/if}

      <div>
        <label for="username" class="block text-sm font-medium mb-1">Username</label>
        <input
          id="username"
          type="text"
          bind:value={username}
          required
          class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
        />
      </div>

      <div>
        <label for="password" class="block text-sm font-medium mb-1">Password</label>
        <input
          id="password"
          type="password"
          bind:value={password}
          required
          class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
        />
      </div>

      <button
        type="submit"
        disabled={submitting}
        class="w-full rounded-lg bg-emerald-600 text-white text-sm font-medium py-2 hover:bg-emerald-700 disabled:opacity-60"
      >
        {submitting ? "Logging in…" : "Log in"}
      </button>
    </form>

    <p class="text-center text-sm text-gray-500 mt-4">
      <a href="/accounts/login/" class="underline">Prefer the classic site?</a>
    </p>
  </div>
</div>
