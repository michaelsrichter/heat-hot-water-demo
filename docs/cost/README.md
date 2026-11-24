# Cost

The demo separates fixed platform cost from use-based AI and data cost.

- [cost-to-run.md](cost-to-run.md) describes the services used today and the
  likely bill drivers.
- [cost-at-scale.md](cost-at-scale.md) explains what to measure at 10x and
  100x usage.

The Bicep budget starts at USD 50 per month. It alerts at 80% of actual spend and
100% of forecasted spend. A budget alert does not stop resources or guarantee a
hard ceiling.

The hosted app can scale to zero when idle. Practice mode makes no paid model
call. The live briefing path creates model usage, so public access remains
bounded by saved scenarios and rate limits.
