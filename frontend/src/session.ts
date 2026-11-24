const key = "heat-hot-water-demo-session";

export function getBrowserSessionId(): string {
  const existing = sessionStorage.getItem(key);
  if (existing) {
    return existing;
  }
  const next = crypto.randomUUID();
  sessionStorage.setItem(key, next);
  return next;
}

