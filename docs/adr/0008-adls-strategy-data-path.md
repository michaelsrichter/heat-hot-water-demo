# ADR 0008: Use ADLS Gen2 as the Strategy data source

- Status: accepted
- Date: 2026-11-19
- Context: The customer requested a Strategy-first architecture. The available
  Fabric capacity cannot create Lakehouse or Warehouse items, while Strategy
  supports Azure Data Lake Storage Gen2 as a file-storage connector.
- Decision: Store versioned current and archived source files in ADLS Gen2.
  Import them into a Strategy Mosaic model, then define relationships and
  hierarchies in Strategy.
- Consequences:
  - Strategy owns the logical model and scheduled import refresh.
  - The source is a scheduled import, not a live query for every user action.
  - Storage is reachable by the external Strategy service but requires
    authenticated least-privilege RBAC.
  - Stable `current/` paths let Strategy refresh without changing file names.
  - Dated `archive/` paths preserve source evidence.
  - Power BI is not part of the final architecture.
