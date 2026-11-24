# HPD Heat and Hot Water demo script

## The story

Strategy defines the facts. Microsoft Foundry explains the evidence. Housing
teams receive a building-level plan they can verify and own.

The message is not "AI makes the decision." The message is "Strategy and
Foundry help officials find the right problem and prepare the next step
faster."

## Before the demo

Open these pages in this order:

1. Azure Storage for the `heat-hot-water` container.
2. The Strategy `Heat and Hot Water Review Model`.
3. The Strategy `Heat and Hot Water Review Dashboard`.
4. The HPD Heat and Hot Water web demo.

The demo's public KPI cards are from the latest governed Strategy export. The
`config/strategy-mcp.json` file records the target read-only Mosaic MCP
connection. The organization still needs to enable the **Use Mosaic MCP Server**
privilege and complete OAuth before the page can query Strategy MCP live.

For a presentation before the HPD model is exposed, run the app with
`STRATEGY_MCP_MODE=mock`. The page shows **Demo response - not a live MCP
call** and exposes the four-step `get_projects → get_models → get_semantics →
query` conversation. The displayed KPI values remain the latest governed
Strategy export; the mocked MCP layer demonstrates the protocol and user
experience, not new calculations.

Know the mode before presenting:

- **Practice mode:** The public totals are a saved public-record snapshot. The
  building records and team assignments are synthetic. The briefing is
  deterministic and costs nothing.
- **Live mode:** The same flow calls the deployed `hpd-review-agent`. Use this
  only after the health check, model, endpoint, and official citations have
  been verified.

## Suggested 8-minute walkthrough

### 1. Start with the business problem — 1 minute

Say:

> New York housing staff receive many reports about heat and hot water. The
> records do not all describe the same thing. A complaint, a problem row, a 311
> request, and a violation are different records. Staff need one trusted set
> of definitions before they ask AI for a recommendation.

Point out the page heading:

> "Turn heat and hot-water complaints into clear next actions."

Explain:

> This demo does not issue a violation or contact a resident. It helps a staff
> member prepare a better-verified follow-up.

### 2. Show the data arriving in Azure — 1 minute

In Azure Storage, open the `heat-hot-water` container and point to these
one-file Strategy folders:

- `strategy-complaints`
- `strategy-violations`
- `strategy-requests-311`
- `strategy-buildings`

Say:

> Azure stores each source at the right grain. A complaint with several problem
> rows is still one complaint. A possible violation stays a possible violation
> until someone verifies the classification.

Open `current/manifest.json` and call out the source window and refresh state.
Do not read storage account IDs or file paths unless the audience asks a
technical question.

### 3. Show the semantic definitions in Strategy — 2 minutes

Open the `Heat and Hot Water Review Model`.

Say:

> Strategy Mosaic is the place where the business definition lives. Microsoft
> Foundry does not make up or recalculate these numbers.

Show one or two definitions:

- **Distinct heat or hot-water complaints:** one complaint ID, not one problem
  row.
- **Buildings with a candidate violation:** buildings with a complaint summary
  and at least one possible heat or hot-water violation.

Then show the shared building relationship and borough attribute.

Say:

> This is important because a violation can appear in the same building
> history without proving that a specific complaint caused it.

Open the `Heat and Hot Water Review Dashboard`. Show that borough totals and
the governed KPI cards use the Mosaic model. Call out the supervisor KPIs:

- unresolved heat or hot-water complaints; and
- unresolved candidate violations.

### 4. Show the same facts in the demo — 1 minute

Switch to the HPD demo and point to "How much heat and hot-water work is still
open?"

Say:

> The web app keeps the same metric names and definitions. Strategy says what
> is still open. Foundry does not recalculate the count.

Explain the data connection honestly:

> The live KPI values come from the latest governed Strategy export. The
> intended live read path is the read-only Strategy Mosaic MCP server. This
> demo labels the current snapshot source and will switch to MCP after the
> organization's OAuth connection is enabled.

Point to the three-step story:

1. Strategy defines the facts.
2. Foundry explains the evidence and official guidance.
3. A housing team receives an owner-ready plan.

### 5. Run the owner-ready review — 2 minutes

Choose a borough or neighborhood, such as **Brooklyn Heights**, and click
**Ask Foundry for a next-step plan**.

Say:

> The request now combines three inputs: the Strategy KPI values and
> definitions, the selected synthetic building records, and current HPD
> guidance links. The AI is asked to explain known facts, unknown facts, and
> the next staff check. It is not asked to decide enforcement.

When the result appears, point out:

- the reconciliation between Strategy and the worklist;
- the cited supervisor briefing;
- the missing information that must be checked; and
- the **Action plan by service area**.

For the Brooklyn example, say:

> A large borough does not need one oversized queue. The demo can route one
> record to the Brooklyn North Response Team and another to the Brooklyn
> Heights Response Team. Smaller service areas can remain borough-wide.

Open one building card and show the ordered steps:

1. assign it to the role-based owner;
2. verify the open status, classification, or missing correction date;
3. review the complaint and violation evidence; and
4. document the official decision outside the demo.

### 6. Close on the business benefit — 1 minute

Say:

> Strategy makes the data answer trustworthy. Microsoft Foundry turns that
> governed answer into a short, cited plan. The staff member still checks the
> source and chooses the official action.

Summarize the benefit:

- less time finding the right records;
- fewer arguments about what a metric means;
- clearer handoff to borough or neighborhood owners; and
- faster follow-up without removing human judgment.

## Questions the audience may ask

### Does the AI calculate the metrics?

No. Strategy Mosaic defines and calculates the metric. Foundry receives that
governed value and explains it.

### Does a complaint cause a violation?

No. The demo does not make that claim. It treats the complaint and violation as
related records in the same building history.

### Does the system issue violations or contact residents?

No. It prepares a suggested follow-up. A housing staff member verifies the
evidence and uses the official system.

### Why show borough and neighborhood owners?

A role-based owner makes the next action clear. Large boroughs can use smaller
service areas such as Brooklyn North or Brooklyn Heights. These labels are
synthetic and do not identify real employees.

### Is the current page using live Foundry?

Check the briefing label:

- **Foundry practice briefing:** deterministic Practice result.
- **Foundry IQ briefing:** live hosted-agent result.

Never describe Practice output as a live model response.

## Presenter close

Leave this sentence on screen:

> One source of truth for the metric, one clear explanation of the evidence,
> and one owner-ready plan for the building.
