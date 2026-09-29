// Browser-side state for the product tour. Storage can be unavailable (private mode,
// blocked site data), so every access is guarded and the tour degrades to "show on demand".

const PENDING = "standardos-tour-pending";
const optOutKey = (identity: string) => `standardos-tour-optout:${identity}`;

function safe<T>(fn: () => T, fallback: T): T {
  try {
    return fn();
  } catch {
    return fallback;
  }
}

/** Called by the router when the user moves from /login or /signup into the app. */
export function markSignIn() {
  safe(() => window.sessionStorage.setItem(PENDING, "1"), undefined);
}

/** True once per sign-in: reading clears the flag. */
export function consumeSignIn(): boolean {
  return safe(() => {
    const pending = window.sessionStorage.getItem(PENDING) === "1";
    window.sessionStorage.removeItem(PENDING);
    return pending;
  }, false);
}

export function showsOnSignIn(identity: string): boolean {
  return safe(() => window.localStorage.getItem(optOutKey(identity)) !== "1", true);
}

export function setShowsOnSignIn(identity: string, show: boolean) {
  safe(() => {
    if (show) window.localStorage.removeItem(optOutKey(identity));
    else window.localStorage.setItem(optOutKey(identity), "1");
  }, undefined);
}
