<script>
  import { onMount } from "svelte";
  import { link } from "svelte-spa-router";
  import { api } from "../lib/api.js";
  import PublicHeader from "../lib/PublicHeader.svelte";
  import PublicFooter from "../lib/PublicFooter.svelte";

  let articles = $state([]);
  let categories = $state([]);
  let activeCategory = $state("");
  let loading = $state(true);
  let error = $state("");

  async function load() {
    loading = true;
    try {
      const data = await api.news(activeCategory);
      articles = data.articles;
      categories = data.categories;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  function selectCategory(value) {
    activeCategory = value;
    load();
  }

  function formatDate(iso) {
    const d = new Date(iso);
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
  }
  function formatTime(iso) {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  }

  onMount(load);
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
  <PublicHeader />

  <div class="max-w-6xl mx-auto px-4 md:px-8 py-10 w-full flex-1">
    <h1 class="text-xl font-semibold mb-4">News</h1>

    <div class="flex flex-wrap gap-2 mb-6">
      <button
        onclick={() => selectCategory("")}
        class="text-xs font-medium px-3 py-1.5 rounded-full {activeCategory === '' ? 'bg-emerald-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}"
      >
        All
      </button>
      {#each categories as c}
        <button
          onclick={() => selectCategory(c.value)}
          class="text-xs font-medium px-3 py-1.5 rounded-full {activeCategory === c.value ? 'bg-emerald-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}"
        >
          {c.label}
        </button>
      {/each}
    </div>

    {#if loading}
      <p class="text-gray-500">Loading…</p>
    {:else if error}
      <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
    {:else if articles.length === 0}
      <p class="text-gray-500">No articles yet.</p>
    {:else}
      <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
        {#each articles as a}
          <a
            href="/news/{a.slug}"
            use:link
            class="block bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden hover:border-emerald-300 dark:hover:border-emerald-800 transition-colors"
          >
            {#if a.image}
              <img src={a.image} alt="" class="w-full h-36 object-cover" />
            {:else}
              <div class="w-full h-36 bg-gradient-to-br from-emerald-50 to-gray-100 dark:from-emerald-950 dark:to-gray-800"></div>
            {/if}
            <div class="p-4">
              <span class="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400">{a.category_display}</span>
              <h2 class="font-semibold mt-1 mb-2 leading-snug">{a.title}</h2>
              <p class="text-sm text-gray-500 line-clamp-2 mb-3">{a.summary}</p>
              <p class="text-xs text-gray-400">{formatDate(a.published_at)} · {formatTime(a.published_at)}</p>
            </div>
          </a>
        {/each}
      </div>
    {/if}
  </div>

  <PublicFooter />
</div>
