# ADR 0007: Evaluate Fabric, but retain an external-SaaS fallback

- Status: superseded by ADR-0008
- Date: 2026-11-18
- Context: The original plan used Microsoft Fabric for governed tables. The
  available Premium-per-user capacity rejected Lakehouse, Warehouse, and
  Notebook item creation.
- Decision: Preserve the Fabric research, but do not make Fabric a runtime
  dependency for the demo.
- Consequences:
  - A Power BI semantic model was created during feasibility work and is not
    used by the final solution.
  - The final path moves to Azure ADLS Gen2 and Strategy Mosaic.

