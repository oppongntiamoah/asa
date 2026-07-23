<script>
  import PublicHeader from "../lib/PublicHeader.svelte";
  import PublicFooter from "../lib/PublicFooter.svelte";

  const faqs = [
    { q: "Are the prices live?", a: "No. GSE publishes closing prices once a day — every price in SikaTrack is labeled with the date it's from." },
    { q: "Is this investment advice?", a: "No. SikaTrack is an informational portfolio tracker, not a licensed investment adviser or broker under Ghanaian securities law." },
    { q: "Which brokers can I upload statements from?", a: "IC Securities and Black Star Advisors today. More brokers are being added over time — you can always add transactions manually in the meantime." },
    { q: "How much does it cost?", a: "SikaTrack is free to use right now. If paid plans launch later, your existing data and free-tier features won't disappear." },
    { q: "How do I delete my account?", a: "Once you're signed in, go to Settings → Danger zone → Request account deletion." },
    { q: "Is my data private?", a: "Yes. Your portfolio is visible only to you, and the app includes a privacy mode to hide amounts on screen when you don't want them visible to someone nearby." },
  ];
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
  <PublicHeader />

  <div class="max-w-2xl mx-auto px-4 md:px-8 py-10 w-full flex-1">
    <h1 class="text-xl font-semibold mb-6">Frequently asked questions</h1>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 space-y-5">
      {#each faqs as f}
        <div>
          <p class="text-sm font-medium">{f.q}</p>
          <p class="text-sm text-gray-500 mt-1">{f.a}</p>
        </div>
      {/each}
    </div>
  </div>

  <PublicFooter />
</div>
