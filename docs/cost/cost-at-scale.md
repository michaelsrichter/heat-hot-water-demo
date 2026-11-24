# Cost at scale

Storage cost changes with retained dated archives, file format, and refresh
frequency. Strategy's scheduled import affects compute in the Strategy
environment, not every visitor.

Measure these cases after deployment:

| Usage | Measure |
|---|---|
| Current demo | Blob GB, write operations, Strategy refresh duration, Log Analytics GB |
| 10x refreshes | Blob operations, Strategy refresh jobs, Container App starts |
| 100x refreshes | Quotas, rate limits, archive retention, and global review run cap |

Delete archives by retention policy only after evidence retention is approved.
Do not increase the archive window merely to preserve every demo run.

