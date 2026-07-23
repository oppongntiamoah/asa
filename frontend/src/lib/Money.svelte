<script>
  import { money } from "./format.js";

  let { value, class: className = "" } = $props();
</script>

<span class="money-mask {className}">{money(value)}</span>
