# Threat model

| Threat | Control | Current state |
|---|---|---|
| Anonymous public reads ADLS | Anonymous Blob access off; Azure jobs use role-based access with Managed Identity | Implemented and data-plane tested |
| Storage shared key is exposed or misused | Disable shared-key authentication in Bicep and use role-based identity access | Implemented |
| Connector credentials are exposed in source or logs | Keep all external connector configuration out of the repository | Implemented |
| Raw PII reaches ADLS | Field allowlist; privacy contract test | Implemented and tested |
| A changed source overwrites evidence | Stable current files plus dated archive copy | Implemented |
| Stale source looks current | Manifest source window and explicit degraded state | API contract implemented |
| A malformed field reaches Strategy | Schema names, CSV types, and grain rules in the model contract | Documented |
| Public users trigger unbounded cost | Fixed scenarios and six-per-minute in-memory Practice limit | Practice only |
| Public app reaches Strategy or ADLS directly | Browser calls only the demo API; raw storage SDK stays server-side | Implemented |
| Strategy uses a local file and cannot refresh | Replace local snapshot with ADLS file-storage tables and schedule refresh | Manual step |

## Network posture

The storage account accepts only Microsoft Entra-authenticated access. Anonymous
Blob access and shared-key authentication stay disabled. The app and ingestion
jobs receive only the data-plane roles they need.

The public deployment code does not create an external Strategy credential.
Production operators must configure that integration under the organization's
approved network and identity controls.

