# ADR 0009: Use a vaulted Shared Key fallback for Strategy

- Status: superseded by [0011](0011-managed-identity-only-public-infrastructure.md)
- Date: 2026-11-19
- Context: Strategy's service-principal connector could read ADLS through the
  Azure control plane, but the connector test required Azure Storage delegated
  consent. The tenant will not grant that consent. Strategy's native Shared Key
  method connected successfully.
- Decision: Use the ADLS storage account Shared Key only for the Strategy
  connector. Store it in Key Vault, keep it out of source and public app
  settings, disable anonymous access, and rotate it when exposure is suspected.
- Consequences:
  - The connection is account-scoped rather than read-only.
  - Strategy could write if a defect or misuse occurs.
  - Key Vault and Strategy's encrypted connector store contain the secret.
  - The tag-maintenance job does not read or expose the key.
  - The service-principal application and unused client secret were removed.

This record describes a private operational choice. The public repository no
longer provisions the connector, its key, or a network-policy bypass.
