import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import App from "./App";
import type { Overview, ReviewRun } from "./types";

const overview: Overview = {
  mode: "practice",
  rule_version: "practice-0.1",
  rule_description: "A provisional practice rule.",
  source_limitations: ["The records are synthetic."],
  scenarios: [
    {
      id: "winter-start",
      title: "Start of the review period",
      kind: "observed_snapshot",
      source_snapshot_date: "2026-01-15",
      simulated_review_date: "2026-01-15",
      eligible_count: 2,
      building_count: 5,
    },
  ],
  service_areas: ["Bronx", "Brooklyn Heights"],
  data_pipeline: {
    architecture:
      "NYC Open Data -> Azure ingestion -> ADLS Gen2 -> Strategy Mosaic -> dashboard and review app",
    mode: "adls-gen2-strategy",
    storage_account: "stexample",
    container: "heat-hot-water",
    manifest_path: "current/manifest.json",
    source_window_start: "2026-11-01T00:00:00",
    source_window_end: "2026-11-19T00:00:00",
    strategy_model: "Heat and Hot Water Review Model",
    strategy_dashboard: "Heat and Hot Water Review Dashboard",
    strategy_refresh: "adls-scheduled",
    strategy_as_of: "2026-11-19",
    strategy_source: "strategy-mosaic-snapshot",
    strategy_mcp_status: "not_configured",
    strategy_mcp_trace: null,
    totals: [
      { label: "Source rows", value: 54684 },
      { label: "Building rows", value: 9058 },
    ],
    kpis: [
      {
        id: "unresolved-complaints",
        label: "Unresolved heat or hot-water complaints",
        value: 4668,
        unit: "complaints",
        definition: "Distinct complaint IDs still marked OPEN.",
        why_it_matters: "This is the main complaint queue.",
        strategy_object: "Open Complaints",
      },
      {
        id: "unresolved-candidate-violations",
        label: "Unresolved candidate violations",
        value: 4503,
        unit: "violations",
        definition: "Distinct candidate violations still marked Open.",
        why_it_matters: "These records may need verification.",
        strategy_object: "Open Candidate Violations",
      },
      {
        id: "distinct-complaints",
        label: "Distinct heat or hot-water complaints",
        value: 25416,
        unit: "complaints",
        definition: "Distinct complaint IDs in the source window.",
        why_it_matters:
          "One complaint is not counted once for every problem row.",
        strategy_object: "Distinct Complaints",
      },
    ],
    borough_metrics: [
      {
        borough: "Bronx",
        distinct_complaints: 10043,
        candidate_violations: 1851,
        unresolved_complaints: 1153,
        unresolved_candidate_violations: 1922,
      },
    ],
    steps: [
      {
        order: 1,
        id: "public-data",
        title: "Read public NYC data",
        owner: "Azure ingestion job",
        detail: "Read public records.",
        status: "ready",
        artifact: "NYC Open Data",
      },
      {
        order: 2,
        id: "prepare",
        title: "Prepare safe source files",
        owner: "Azure ingestion job",
        detail: "Keep source grains separate.",
        status: "ready",
        artifact: "current/*.csv",
      },
      {
        order: 3,
        id: "store",
        title: "Write ADLS Gen2 snapshots",
        owner: "Azure",
        detail: "Write stable current files.",
        status: "ready",
        artifact: "adls://heat-hot-water/current/",
      },
      {
        order: 4,
        id: "connect",
        title: "Connect Strategy to ADLS",
        owner: "Strategy operator",
        detail: "Use four connected ADLS table folders.",
        status: "configured",
        artifact: "Strategy file storage",
      },
      {
        order: 5,
        id: "model",
        title: "Create Mosaic relationships",
        owner: "Strategy",
        detail: "Map building IDs.",
        status: "configured",
        artifact: "Heat and Hot Water Review Model",
      },
      {
        order: 6,
        id: "briefing",
        title: "Prepare a cited briefing",
        owner: "Foundry IQ",
        detail: "Explain the governed facts.",
        status: "configured",
        artifact: "HPD Review Agent",
      },
      {
        order: 7,
        id: "present",
        title: "Let an HPD official review",
        owner: "Housing staff",
        detail: "Check the facts before acting.",
        status: "configured",
        artifact: "Case review list",
      },
    ],
    limitations: ["The review rule is provisional."],
  },
  strategy_connection: "adls_scheduled",
  foundry_connection: "not_configured",
};

const review: ReviewRun = {
  scenario_id: "winter-start",
  mode: "practice",
  started_at: "2026-11-18T12:00:00Z",
  completed_at: "2026-11-18T12:00:01Z",
  rule_version: "practice-0.1",
  steps: ["Checked the saved source snapshot.", "Prepared the review items."],
  eligible_count: 1,
  strategy_count: 1,
  briefing: {
    mode: "practice",
    provider: "Deterministic Foundry practice agent",
    text: "What Strategy Mosaic shows\n- A governed complaint count.",
    citations: [],
  },
  items: [
    {
      building_id: "BLD-101",
      building_label: "River Court",
      borough: "Bronx",
      service_area: "Bronx",
      owner_team: "Bronx Response Team",
      state: "new",
      trigger: "The recorded correction date passed.",
      rule_version: "practice-0.1",
      observed_facts: ["The violation is recorded as open."],
      unknowns: [],
      suggested_follow_up: "Check the source records.",
      action_plan: [
        "Assign this record to the Bronx Response Team.",
        "Confirm the violation is still open.",
      ],
      source_snapshot_date: "2026-01-15",
      simulated_review_date: "2026-01-15",
      citations: [
        {
          title: "Practice building record",
          url: "/docs/practice-data",
          scope: "data",
          passage: "Synthetic record.",
        },
      ],
    },
  ],
};

afterEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
});

test("loads the practice overview and runs a bounded review", async () => {
  vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(
      new Response(JSON.stringify(overview), { status: 200 }),
    )
    .mockResolvedValueOnce(
      new Response(JSON.stringify(review), { status: 200 }),
    );

  render(<App />);

  expect(
    await screen.findByRole("heading", {
      name: "Turn heat and hot-water complaints into clear next actions.",
    }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("heading", {
      name: "The right answer starts with the right facts",
    }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("heading", {
      name: "How a complaint becomes a clear review list",
    }),
  ).toBeInTheDocument();
  expect(screen.getByText("25,416")).toBeInTheDocument();
  expect(screen.getByText("4,668")).toBeInTheDocument();
  expect(screen.getByText("4,503")).toBeInTheDocument();
  expect(
    screen.getByRole("heading", {
      name: "How much heat and hot-water work is still open?",
    }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("heading", {
      name: "Choose your area and get a next-step plan",
    }),
  ).toBeInTheDocument();
  expect(screen.getAllByText("Strategy Mosaic")).not.toHaveLength(0);
  expect(screen.getByText("Microsoft AI + Strategy")).toBeInTheDocument();
  expect(
    screen.queryByText("Show the simulated Strategy MCP conversation"),
  ).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Documentation" })).toHaveAttribute(
    "href",
    "/docs/",
  );

  await userEvent.selectOptions(
    screen.getByRole("combobox", { name: "Your borough or neighborhood" }),
    "Bronx",
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Ask Foundry for a next-step plan" }),
  );

  expect(
    await screen.findByRole("heading", {
      name: "Next steps for Bronx",
    }),
  ).toBeInTheDocument();
  expect(screen.getAllByText("River Court")).not.toHaveLength(0);
  expect(screen.getAllByText("Open item")).not.toHaveLength(0);
  expect(screen.getAllByText("Bronx Response Team")).not.toHaveLength(0);
  expect(
    screen.getByRole("heading", { name: "Action plan by service area" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("heading", {
      name: "What Foundry recommends checking next",
    }),
  ).toBeInTheDocument();
  await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(2));
  const request = vi.mocked(globalThis.fetch).mock.calls[1]?.[1];
  expect(JSON.parse(String(request?.body))).toMatchObject({
    scenario_id: "winter-start",
    service_area: "Bronx",
  });
});

test("shows a usable load error instead of a false practice result", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ detail: "Practice data is unavailable." }), {
      status: 503,
    }),
  );

  render(<App />);

  expect(
    await screen.findByText("Practice data is unavailable."),
  ).toBeInTheDocument();
  expect(
    screen.queryByText("Next steps for all practice areas"),
  ).not.toBeInTheDocument();
});
