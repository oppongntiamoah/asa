<script>
  import { onMount } from "svelte";

  let deferredEvent = $state(null);
  let dismissed = $state(false);

  onMount(() => {
    const handler = (event) => {
      event.preventDefault();
      deferredEvent = event;
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  });

  async function install() {
    if (!deferredEvent) return;
    deferredEvent.prompt();
    await deferredEvent.userChoice;
    deferredEvent = null;
  }
</script>

{#if deferredEvent && !dismissed}
  <div class="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-lg px-4 py-3">
    <p class="text-sm">Install SikaTrack for quick, offline-friendly access.</p>
    <button onclick={install} class="text-sm font-medium bg-emerald-600 text-white px-3 py-1.5 rounded-lg hover:bg-emerald-700">
      Install
    </button>
    <button onclick={() => (dismissed = true)} aria-label="Dismiss" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
      &times;
    </button>
  </div>
{/if}
