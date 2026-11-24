# Evaluations

This folder holds evaluation suites for AI-assisted features (per
[`eps-demo-ai-models`](../.github/skills/eps-demo-ai-models/SKILL.md)). It
exists even while empty to signal intent — every EPS AI demo should have
somewhere to put evals the moment it grows an AI feature.

When you add one:

- Assert against the deterministic `FAKE_AI=1` fixtures under
  `tests/fixtures/ai/` for fast, free, CI-safe runs.
- Cover the failure modes that matter most for the feature (hallucinated
  results outside an allowed set, ignoring hard constraints, unusable output
  shape, etc.).
- When evals exist, wire them into CI as a non-blocking check or scheduled job —
  don't gate merges on eval scores.

For evaluations graded and saved in Microsoft Foundry, with an Evaluations page
in the app, see the opt-in skill
[`eps-demo-evaluations`](../.github/skills/eps-demo-evaluations/SKILL.md). Use
it only when the demo's owner asks for it.
