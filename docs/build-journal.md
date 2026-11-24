# Build journal

## 18 November 2026

- Cloned the EPS demo template into `C:\src\heat-hot-water-demo`.
- Built the local React/FastAPI Practice experience and saved Strategy model and
  dashboard assets.
- Tested Microsoft Fabric and Power BI feasibility. The PPU capacity rejected
  Lakehouse, Warehouse, and Notebook creation.
- Confirmed the tenant could store a Power BI push model. That model is not used
  by the final Strategy-first architecture.

## 19 November 2026

- Selected Azure Data Lake Storage Gen2 as the supported Strategy file-storage
  path.
- Added ADLS Gen2, hierarchical namespace, RBAC, diagnostics, and app manifest
  configuration to Bicep.
- Added an Azure ingestion module that writes:
  - `current/complaint-problems.csv`;
  - `current/violation-candidates.csv`;
  - `current/requests-311.csv`;
  - `current/building-review.csv`;
  - `current/manifest.json`; and
  - matching dated `archive/` files.
- Added process-contract and ingestion tests.
- Added a six-step process view to the public app.
- Updated architecture, sequence, data-flow, identity, privacy, cost, and
  Strategy setup diagrams and documentation.
- Provisioned an ADLS Gen2 account and the `heat-hot-water` container. The
  account has a hierarchical namespace, anonymous access disabled, and managed
  identity access.
- Verified the Strategy dashboard and Mosaic model persisted, and captured the
  hierarchy view showing the `Borough -> Building` relationship.
- Uploaded 5 current files and a matching 5-file dated archive to ADLS. The
  current paths include 25,654 complaint rows, 3,684 candidate violations,
  25,346 311 requests, 9,058 building rows, and the manifest.
- Added four one-file Strategy folders to ADLS, removed the old local-file
  table, imported all four ADLS tables, merged shared Building and Borough
  attributes, rebuilt the dashboard, and saved **Heat and Hot Water Daily
  Refresh**. It has a Daily
  schedule with `Replace existing data` on all four source folders. The
  subscription's next run and manual Run Now control are visible in Strategy.
