# Security

The app separates public input, governed data, model access, and staff review.

| Document | What it covers |
|---|---|
| [threat-model.md](threat-model.md) | threats, controls, accepted risks, and network posture |
| [auth.md](auth.md) | Azure identities and the active Strategy connector |
| [secrets.md](secrets.md) | the boundary for credentials and source control |
| [content-filtering.md](content-filtering.md) | Microsoft Foundry content safety |
| [rate-limiting.md](rate-limiting.md) | public review limits and production gaps |
| [privacy.md](privacy.md) | field allowlist, browser state, and excluded data |

The public deployment uses Managed Identity for Azure services. Anonymous Blob
access and storage shared-key authentication are disabled.

An external Strategy connector is environment-specific. The deployment operator
configures it outside this repository with approved identity, secret, and network
controls. The public page never receives a connector credential. It also never
asks Foundry to decide a legal or enforcement action.
