# Strategy ADLS setup

## Connection boundary

The public repository does not create or store a Strategy credential. Get the
deployment's storage account name from `azd env get-value
DATA_STORAGE_ACCOUNT_NAME`. Configure the approved connector identity and any
credential outside source control.

Do not publish connector screenshots that show usernames, passwords, tokens,
subscription IDs, or storage secrets.

## ADLS source folders

Strategy reads one table folder at a time:

| Strategy folder | Table | Grain |
|---|---|---|
| `strategy-buildings` | `building-review.csv` | one building |
| `strategy-complaints` | `complaint-problems.csv` | one problem row |
| `strategy-violations` | `violation-candidates.csv` | one candidate violation |
| `strategy-requests-311` | `requests-311.csv` | one 311 request |

The old local-file building snapshot was removed from the Mosaic model.

## Completed model work

Strategy applies the merged attributes:

| Attribute | Key | Parent |
|---|---|---|
| Borough | `borough` | none |
| Building | `building_id` / `buildingid` | Borough |
| Complaint | `complaint_id` | Building |
| Violation Candidate | `violationid` | Building |
| 311 Request | `unique_key` | Building |

Measures:

- **Distinct Complaints** = distinct `complaint_id`;
- **Candidate Violation Count** = distinct candidate `violationid`; and
- **Review State** = building-level `needs_verification`.

The model has four ADLS source tables and uses `Replace existing data` for each.

## Completed refresh schedule

- Schedule: `Daily`;
- name: `Heat and Hot Water Daily Refresh`;
- model policy: `Replace existing data`;
- tables: all four Strategy folders.

## Reconciled dashboard

| Borough | Distinct complaints | Candidate violations |
|---|---:|---:|
| Bronx | 8,424 | 1,525 |
| Brooklyn | 7,238 | 782 |
| Manhattan | 6,171 | 808 |
| Queens | 3,383 | 306 |
| Staten Island | 200 | 35 |

The dashboard is saved from the ADLS-backed model. Candidate violation totals
reflect the latest refreshed source snapshot and remain provisional.

## Credential maintenance

The public deployment disables storage shared-key authentication. Follow the
organization's approved identity process when the external Strategy connection
needs rotation. Test the connection, run one manual model refresh, and keep all
credential values outside the repository.
