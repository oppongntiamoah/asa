<script>
  const faqs = [
    { q: "Are the prices live?", a: "No. GSE publishes closing prices once a day — every price in SikaTrack is labeled with the date it's from." },
    { q: "Is this investment advice?", a: "No. SikaTrack is an informational portfolio tracker, not a licensed investment adviser or broker under Ghanaian securities law." },
    { q: "Which brokers can I upload statements from?", a: "IC Securities and Black Star Advisors today. More brokers are being added over time — you can always add transactions manually in the meantime." },
    { q: "How do I delete my account?", a: "Go to Settings → Danger zone → Request account deletion." },
  ];
</script>

<h1 class="text-xl font-semibold mb-6">Support</h1>

<div class="bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-900 rounded-xl p-4 mb-6 text-sm text-amber-800 dark:text-amber-300">
  Placeholder contact details below — replace with real ones before launch.
</div>

<div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 mb-6">
  <p class="text-sm font-semibold mb-2">Contact us</p>
  <p class="text-sm text-gray-600 dark:text-gray-400">Email: <span class="text-gray-400">support@sikatrack.example</span></p>
  <p class="text-sm text-gray-600 dark:text-gray-400">Telegram: <span class="text-gray-400">@sikatrack_support</span></p>
</div>

<div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 space-y-4">
  <p class="text-sm font-semibold">Frequently asked questions</p>
  {#each faqs as f}
    <div>
      <p class="text-sm font-medium">{f.q}</p>
      <p class="text-sm text-gray-500">{f.a}</p>
    </div>
  {/each}
</div>
