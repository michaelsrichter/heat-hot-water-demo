export type ScenarioSummary = {
  id: string;
  title: string;
  kind: "observed_snapshot" | "synthetic_overlay";
  source_snapshot_date: string;
  simulated_review_date: string;
  eligible_count: number;
  building_count: number;
};

export type Overview = {
  mode: "practice";
  rule_version: string;
  rule_description: string;
  source_limitations: string[];
  scenarios: ScenarioSummary[];
  service_areas: string[];
  data_pipeline: DataPipeline;
  strategy_connection: "not_configured" | "snapshot" | "adls_scheduled";
  foundry_connection: "not_configured" | "configured";
};

export type PipelineStep = {
  order: number;
  id: string;
  title: string;
  owner: string;
  detail: string;
  status:
    | "ready"
    | "configured"
    | "blocked"
    | "snapshot"
    | "not_configured"
    | "needs_action";
  artifact: string;
};

export type DataPipeline = {
  architecture: string;
  mode: "adls-gen2-strategy";
  storage_account: string;
  container: string;
  manifest_path: string;
  source_window_start: string;
  source_window_end: string;
  strategy_model: string;
  strategy_dashboard: string;
  strategy_refresh: "adls-scheduled";
  strategy_as_of: string;
  strategy_source:
    | "strategy-mosaic-snapshot"
    | "strategy-mosaic-mcp"
    | "strategy-mosaic-mcp-mock";
  strategy_mcp_status: "configured" | "not_configured" | "mock";
  strategy_mcp_trace: StrategyMcpTrace | null;
  totals: Array<{ label: string; value: number }>;
  kpis: PipelineKpi[];
  borough_metrics: BoroughMetric[];
  steps: PipelineStep[];
  limitations: string[];
};

export type StrategyMcpTrace = {
  mode: "mock" | "live";
  project: string;
  model: string;
  notice: string;
  trace: Array<{
    tool: string;
    purpose: string;
    request: Record<string, unknown>;
    response_preview: string;
  }>;
};

export type BoroughMetric = {
  borough: string;
  distinct_complaints: number;
  candidate_violations: number;
  unresolved_complaints: number;
  unresolved_candidate_violations: number;
};

export type PipelineKpi = {
  id: string;
  label: string;
  value: number;
  unit: string;
  definition: string;
  why_it_matters: string;
  strategy_object: string;
};

export type Citation = {
  title: string;
  url: string;
  scope: "data" | "guidance";
  passage: string;
};

export type ReviewItem = {
  building_id: string;
  building_label: string;
  borough: string;
  service_area: string;
  owner_team: string;
  state: "new" | "carried_forward" | "needs_verification";
  trigger: string;
  rule_version: string;
  observed_facts: string[];
  unknowns: string[];
  suggested_follow_up: string;
  action_plan: string[];
  source_snapshot_date: string;
  simulated_review_date: string;
  citations: Citation[];
};

export type ReviewRun = {
  scenario_id: string;
  mode: "practice";
  started_at: string;
  completed_at: string;
  rule_version: string;
  steps: string[];
  eligible_count: number;
  strategy_count: number;
  items: ReviewItem[];
  briefing: Briefing | null;
};

export type Briefing = {
  mode: "practice" | "live";
  provider: string;
  text: string;
  citations: Citation[];
};
