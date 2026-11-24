# Data flow

## 1. Read public sources

The Azure ingestion process reads:

- HPD complaints and problems;
- HPD housing-code violation candidates; and
- NYC 311 heat and hot-water requests.

The allowlist excludes apartments, addresses, coordinates, person fields, owner
details, and 311 resolution text.

## 2. Preserve source grain

The process writes separate current files:

| Path | Grain |
|---|---|
| `current/complaint-problems.csv` | One problem record |
| `current/violation-candidates.csv` | One candidate violation |
| `current/requests-311.csv` | One 311 request |
| `current/building-review.csv` | One building |
| `current/manifest.json` | One ingestion run |

The same CSVs are copied to one-file Strategy folders:
`strategy-buildings/`, `strategy-complaints/`, `strategy-violations/`, and
`strategy-requests-311/`. This layout meets Strategy's requirement that a
folder share one file type and schema.

The same files are copied under `archive/YYYY-MM-DD/`.

## 3. Create building facts

The building summary counts distinct `complaint_id`, not problem rows. Violation
text search creates candidates only. The process does not join one complaint to
one violation.

Every candidate uses `needs_review` and every review state uses
`needs_verification` until a qualified owner approves the rule.

## 4. Import into Strategy

Strategy's Azure Data Lake Storage Gen2 connector reads the stable current
files. The Mosaic model maps `building_id` across the source tables.

The intended hierarchy is:

- `Borough`;
- `Building`; and
- source facts such as Complaint, Candidate Violation, and 311 Request.

## 5. Refresh and present

Strategy schedules the Mosaic import refresh. The dashboard and review service
must use the same `rule_version` and source window. If the manifest is stale or
incomplete, the app must show a degraded state.

## 6. Prepare a cited briefing

The public app sends the governed Strategy metrics, synthetic practice record,
and allowed citations to the `hpd-review-agent`.

The agent explains:

- what the Strategy metric shows;
- what remains unknown;
- which source and official HPD guidance to verify; and
- a possible staff follow-up.

The agent cannot issue a violation, contact a resident, recalculate a Strategy
metric, or choose a legal action. In local Practice mode, a deterministic
provider returns the same shape without calling a paid model.

## 7. Staff review

A housing staff member checks the evidence and makes the official decision
outside the demo. The review list is not a legal or emergency-response queue.

