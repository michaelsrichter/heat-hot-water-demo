# Health

The local `/health` response reports `available` for Practice. It means the saved
fictional data and deterministic rule are usable. It does not prove that ADLS,
Strategy, or Foundry is live.

| Component | Current state |
|---|---|
| Practice data | configured |
| ADLS manifest | configured only when `ADLS_ACCOUNT_URL` is set |
| Strategy | daily ADLS refresh configured |
| Foundry | deployed `hpd-review-agent`; public review returns a live briefing |

Before release, add ADLS freshness checks, Strategy expected-denial probes, and
guidance retrieval without paid model inference. Cache and coalesce health
probes. Never schedule paid model calls just to paint a component green.

If ADLS is configured and `current/manifest.json` cannot be read, `/api/overview`
fails with a clear unavailable state. It must not serve old source metadata as
current.
