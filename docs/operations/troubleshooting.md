# Troubleshooting

## ADLS data-plane access is blocked by network rules

Check the storage account network rules and the caller's Microsoft Entra
role assignment. Do not enable anonymous access or storage shared-key
authentication. Route approved private connectivity through the
organization's network controls.

## The Strategy connector cannot browse ADLS

Check all of these:

1. The storage account has hierarchical namespace enabled.
2. The external connector uses the organization's approved identity.
3. The container is `heat-hot-water`.
4. No connector credential is stored in the repository or public app.

## The upload fails with AuthorizationPermissionMismatch

The local or managed identity needs Storage Blob Data Contributor. Do not use a
storage key as a workaround. Confirm the role assignment has finished
propagating.

## The Strategy model does not refresh

Local-file tables cannot be scheduled. The Strategy Mosaic tables must come from
the ADLS Gen2 file-storage connector and point to the stable `current/` files.

## The app says the manifest is unavailable

Check:

- `ADLS_ACCOUNT_URL`;
- `ADLS_CONTAINER`;
- `current/manifest.json`; and
- the app identity's Storage Blob Data Reader or Contributor role.

The app does not silently fall back to old data. It reports a degraded source.

## The counts changed

Check the snapshot start and end, the distinct complaint rule, and the current
NYC source update time. Do not compare one 20-day window with another period as
if they had the same coverage.

