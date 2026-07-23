<script>
  import { onMount } from "svelte";
  import { link } from "svelte-spa-router";
  import { api } from "../lib/api.js";
  import PublicHeader from "../lib/PublicHeader.svelte";
  import PublicFooter from "../lib/PublicFooter.svelte";

  let { params } = $props();

  let article = $state(null);
  let error = $state("");
  let loading = $state(true);
  let copied = $state(false);

  function formatDate(iso) {
    const d = new Date(iso);
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
  }
  function formatTime(iso) {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  }

  async function load() {
    loading = true;
    error = "";
    try {
      article = await api.newsArticle(params.slug);
    } catch (err) {
      error = err.message || "Couldn't load this article.";
    } finally {
      loading = false;
    }
  }

  function shareUrl() {
    return window.location.href;
  }

  function shareToX() {
    const text = encodeURIComponent(article.title);
    const url = encodeURIComponent(shareUrl());
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, "_blank", "noopener,noreferrer");
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(shareUrl());
      copied = true;
      setTimeout(() => (copied = false), 2000);
    } catch {
      // Clipboard API unavailable (e.g. insecure context) — nothing to fall
      // back to gracefully here, so just leave the button unchanged.
    }
  }

  onMount(load);
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
  <PublicHeader />

  <div class="max-w-2xl mx-auto px-4 md:px-8 py-10 w-full flex-1">
    <a href="/news" use:link class="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-4 inline-flex items-center gap-1">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
      All news
    </a>

    {#if loading}
      <p class="text-gray-500">Loading…</p>
    {:else if error}
      <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
    {:else}
      <article>
        <span class="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400">{article.category_display}</span>
        <h1 class="text-2xl font-bold mt-2 mb-2 leading-snug">{article.title}</h1>
        <p class="text-sm text-gray-400 mb-6">{formatDate(article.published_at)} · {formatTime(article.published_at)}</p>

        {#if article.image}
          <img src={article.image} alt="" class="w-full rounded-xl mb-6 object-cover max-h-96" />
        {/if}

        <div class="text-[15px] leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-line mb-8">{article.body}</div>

        {#if article.source_url}
          <p class="text-sm text-gray-500 mb-8">
            Source: <a href={article.source_url} target="_blank" rel="noopener noreferrer" class="text-emerald-700 dark:text-emerald-400 hover:underline">{article.source_url}</a>
          </p>
        {/if}

        <div class="flex items-center gap-3 border-t border-gray-200 dark:border-gray-800 pt-6">
          <button
            onclick={shareToX}
            class="flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-900"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="w-4 h-4" fill="currentColor">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
            </svg>
            Share to X
          </button>
          <button
            onclick={copyLink}
            class="flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-900"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 010 5.656l-3 3a4 4 0 01-5.656-5.656l1.5-1.5M10.172 13.828a4 4 0 010-5.656l3-3a4 4 0 015.656 5.656l-1.5 1.5" />
            </svg>
            {copied ? "Copied!" : "Copy link"}
          </button>
        </div>
      </article>
    {/if}
  </div>

  <PublicFooter />
</div>
