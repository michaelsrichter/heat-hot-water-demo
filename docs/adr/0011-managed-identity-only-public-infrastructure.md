# ADR 0011: Keep the public deployment identity-only

- Status: accepted
- Date: 2026-11-24
- Context: The demo is published from a public repository. Deployment-specific
  identifiers, connector credentials, personal ownership records, and policy
  bypass automation must not be part of public history.
- Decision: Publish identity-only Bicep. Disable anonymous Blob access and
  shared-key storage authentication. Keep external connector credentials and
  live resource IDs in the authorized deployment environment.
- Consequences:
  - Good: a public clone contains no storage key, connector password, or live
    Azure resource identifier.
  - Good: the data plane uses Microsoft Entra role assignments and managed
    identity.
  - Bad: an external Strategy connector needs a separate, approved operator
    setup.
  - Mitigation: the public runbook explains the boundary without publishing
    connector values.
