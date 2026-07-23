import { writable } from "svelte/store";

const STORAGE_KEY = "sikatrack-privacy";

function loadStored() {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(STORAGE_KEY) === "1";
}

function apply(hidden) {
  document.documentElement.classList.toggle("privacy-mode", hidden);
}

export const privacyMode = writable(loadStored());

if (typeof window !== "undefined") {
  apply(loadStored());
  privacyMode.subscribe((hidden) => {
    localStorage.setItem(STORAGE_KEY, hidden ? "1" : "0");
    apply(hidden);
  });
}

export function togglePrivacy() {
  privacyMode.update((v) => !v);
}
