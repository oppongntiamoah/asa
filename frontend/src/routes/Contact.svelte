<script>
  import PublicHeader from "../lib/PublicHeader.svelte";
  import PublicFooter from "../lib/PublicFooter.svelte";
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
  <PublicHeader />

  <div class="max-w-2xl mx-auto px-4 md:px-8 py-10 w-full flex-1">
    <h1 class="text-xl font-semibold mb-6">Contact</h1>

    <div class="bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-900 rounded-xl p-4 mb-6 text-sm text-amber-800 dark:text-amber-300">
      Placeholder contact details below — replace with real ones before launch.
    </div>

    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 space-y-2">
      <p class="text-sm font-semibold mb-2">Get in touch</p>
      <p class="text-sm text-gray-600 dark:text-gray-400">Email: <span class="text-gray-400">support@sikatrack.example</span></p>
      <p class="text-sm text-gray-600 dark:text-gray-400">Telegram: <span class="text-gray-400">@sikatrack_support</span></p>
    </div>
  </div>

  <PublicFooter />
</div>
