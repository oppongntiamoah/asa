import { writable } from "svelte/store";
import { api, ApiError } from "./api.js";

// null = unknown (still checking), false = not authenticated, object = user
export const user = writable(null);

export async function checkAuth() {
  try {
    const me = await api.me();
    user.set(me);
    return me;
  } catch (err) {
    user.set(false);
    return false;
  }
}

export async function login(username, password) {
  const me = await api.login(username, password);
  user.set(me);
  return me;
}

export async function logout() {
  try {
    await api.logout();
  } finally {
    user.set(false);
  }
}

export { ApiError };
