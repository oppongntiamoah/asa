import { writable } from "svelte/store";

const STORAGE_KEY = "sikatrack-theme";
const media = typeof window !== "undefined" ? window.matchMedia("(prefers-color-scheme: dark)") : null;

function systemPrefersDark() {
  return media ? media.matches : false;
}

function loadStored() {
  if (typeof window === "undefined") return "system";
  return localStorage.getItem(STORAGE_KEY) || "system";
}

// 'light' | 'dark' | 'system'
export const theme = writable(loadStored());

function effective(value) {
  return value === "system" ? (systemPrefersDark() ? "dark" : "light") : value;
}

function apply(value) {
  const root = document.documentElement;
  root.classList.toggle("dark", effective(value) === "dark");
}

if (typeof window !== "undefined") {
  apply(loadStored());
  theme.subscribe((value) => {
    localStorage.setItem(STORAGE_KEY, value);
    apply(value);
  });
  media?.addEventListener("change", () => {
    theme.update((value) => {
      if (value === "system") apply(value);
      return value;
    });
  });
}

export function cycleTheme() {
  theme.update((value) => (value === "system" ? "light" : value === "light" ? "dark" : "system"));
}
