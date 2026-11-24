import type { Overview, ReviewRun } from "./types";

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(
      payload?.detail ?? `Request failed with status ${response.status}.`,
    );
  }
  return (await response.json()) as T;
}

export async function getOverview(): Promise<Overview> {
  return readJson<Overview>(await fetch("/api/overview"));
}

export async function runReview(
  scenarioId: string,
  sessionId: string,
  serviceArea?: string,
): Promise<ReviewRun> {
  return readJson<ReviewRun>(
    await fetch("/api/reviews/run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Demo-Session": sessionId,
      },
      body: JSON.stringify({
        scenario_id: scenarioId,
        service_area: serviceArea,
      }),
    }),
  );
}
