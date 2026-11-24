# Architecture and process diagram

## Data path

```mermaid
flowchart TB
    subgraph Sources
      C[HPD complaints and problems]
      V[HPD violation candidates]
      R[NYC 311 requests]
    end

    subgraph Azure["Azure resource group"]
      J[Ingestion process]
      S[(ADLS Gen2 with hierarchical namespace)]
      Q[current/manifest.json]
      L[Log Analytics and App Insights]
      A[Demo API and UI]
    end

    subgraph Strategy
      X[ADLS Gen2 file-storage connector]
      M[Mosaic logical model]
      H[Relationships and hierarchies]
      D[Heat and Hot Water dashboard]
    end

    C --> J
    V --> J
    R --> J
    J -->|current CSV files| S
    J -->|dated archive| S
    J --> Q
    S -.->|scheduled import| X
    X --> M
    M --> H
    H --> D
    Q --> A
    M --> A
    A --> L
```

Solid arrows show internal data movement. The dashed ADLS-to-Strategy line is a
scheduled import. Strategy does not query Blob Storage for every visitor request.

## Mosaic logical model

```mermaid
flowchart TB
    BO[Borough] --> B[Building]
    B --> CP[Complaint problem facts]
    B --> VV[Violation candidate facts]
    B --> RR[311 supporting facts]
    B --> BS[Building review summary]
```

`building_id` is the shared key. Complaint problems can appear more than once
for one complaint, so the model must count distinct `complaint_id`.

## Operational sequence

```mermaid
sequenceDiagram
    participant Public as NYC Open Data
    participant Azure as Azure ingestion
    participant ADLS as ADLS Gen2
    participant Strategy as Strategy Mosaic
    participant Visitor as Demo visitor

    Public->>Azure: Read approved fields
    Azure->>Azure: Validate grain and PII allowlist
    Azure->>ADLS: Write current files and dated archive
    Strategy->>ADLS: Scheduled import
    Strategy->>Strategy: Apply relationships and rule version
    Visitor->>Strategy: View saved dashboard
    Visitor->>Azure: Run bounded Practice review
```

