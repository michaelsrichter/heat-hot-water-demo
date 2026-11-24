# ADR 0010: Use a hosted agent that cannot recalculate Strategy metrics

- Status: accepted
- Date: 2026-11-19
- Context: Housing staff need a plain-language explanation of the governed
  Strategy snapshot, missing details, and linked HPD guidance. The agent must
  not invent metrics or make enforcement decisions.
- Decision: Use a Microsoft Foundry hosted agent with the Responses protocol.
  Strategy Mosaic remains the source of metric definitions and values.
  The agent receives only safe evidence and approved citations.
- Consequences:
  - The same Strategy metric meaning appears in the dashboard, app, and
    briefing.
  - The agent code is configuration-driven and can be deployed from `azure.yaml`.
  - Local and CI tests use the deterministic Practice provider instead of a
    paid model.
  - A staff member must verify every suggested follow-up before taking action.
  - Live use is deployed with separate consumer and model-inference identities.
