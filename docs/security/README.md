# Security

The app separates public input, governed data, model access, and staff review.

| Document | What it covers |
|---|---|
| [threat-model.md](threat-model.md) | threats, controls, accepted risks, and network posture |
| [auth.md](auth.md) | Azure identities and the active Strategy connector |
| [secrets.md](secrets.md) | Key Vault use and account-key handling |
| [content-filtering.md](content-filtering.md) | Microsoft Foundry content safety |
| [rate-limiting.md](rate-limiting.md) | public review limits and production gaps |
| [privacy.md](privacy.md) | field allowlist, browser state, and excluded data |

The current standard is Managed Identity for Azure services. The Strategy
connector is the one documented exception. It uses a Key Vault-backed ADLS
Shared Key because the tenant does not allow delegated Storage consent.

The public page never receives a storage credential. It also never asks Foundry
to decide a legal or enforcement action.
