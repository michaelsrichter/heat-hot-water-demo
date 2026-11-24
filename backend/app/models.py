from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ViolationSnapshot(BaseModel):
    violation_id: str
    status: Literal["open", "closed", "unknown"]
    recorded_correct_by_date: date | None
    correction_recorded_date: date | None = None
    classification: Literal["approved_heat_or_hot_water", "other", "needs_review"]


class BuildingSnapshot(BaseModel):
    building_id: str
    label: str
    borough: str
    service_area: str
    owner_team: str
    distinct_complaints: int = Field(ge=0)
    complaint_window_days: int = Field(gt=0)
    source_snapshot_date: date
    violation: ViolationSnapshot


class Scenario(BaseModel):
    id: str
    title: str
    kind: Literal["observed_snapshot", "synthetic_overlay"]
    source_snapshot_date: date
    simulated_review_date: date
    buildings: list[BuildingSnapshot]


class Citation(BaseModel):
    title: str
    url: str
    scope: Literal["data", "guidance"]
    passage: str


class ReviewItem(BaseModel):
    building_id: str
    building_label: str
    borough: str
    service_area: str
    owner_team: str
    state: Literal["new", "carried_forward", "needs_verification"]
    trigger: str
    rule_version: str
    observed_facts: list[str]
    unknowns: list[str]
    suggested_follow_up: str
    action_plan: list[str]
    source_snapshot_date: date
    simulated_review_date: date
    citations: list[Citation]


class ReviewRun(BaseModel):
    scenario_id: str
    mode: Literal["practice"]
    started_at: str
    completed_at: str
    rule_version: str
    steps: list[str]
    eligible_count: int
    strategy_count: int
    items: list[ReviewItem]
    briefing: "Briefing | None" = None


class Briefing(BaseModel):
    mode: Literal["practice", "live"]
    provider: str
    text: str
    citations: list[Citation]


class ReviewRequest(BaseModel):
    scenario_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")
    service_area: str | None = Field(
        default=None, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9 -]+$"
    )


class ScenarioSummary(BaseModel):
    id: str
    title: str
    kind: Literal["observed_snapshot", "synthetic_overlay"]
    source_snapshot_date: date
    simulated_review_date: date
    eligible_count: int
    building_count: int


class PipelineTotal(BaseModel):
    label: str
    value: int


class PipelineStep(BaseModel):
    order: int
    id: str
    title: str
    owner: str
    detail: str
    status: Literal[
        "ready", "configured", "blocked", "snapshot", "not_configured", "needs_action"
    ]
    artifact: str


class PipelineKpi(BaseModel):
    id: str
    label: str
    value: int
    unit: str
    definition: str
    why_it_matters: str
    strategy_object: str


class BoroughMetric(BaseModel):
    borough: str
    distinct_complaints: int = Field(ge=0)
    candidate_violations: int = Field(ge=0)
    unresolved_complaints: int = Field(ge=0)
    unresolved_candidate_violations: int = Field(ge=0)


class StrategyMcpTraceStep(BaseModel):
    tool: str
    purpose: str
    request: dict[str, object]
    response_preview: str


class StrategyMcpTrace(BaseModel):
    mode: Literal["mock", "live"]
    project: str
    model: str
    notice: str
    trace: list[StrategyMcpTraceStep]


class DataPipeline(BaseModel):
    architecture: str
    mode: Literal["adls-gen2-strategy"]
    storage_account: str
    container: str
    manifest_path: str
    source_window_start: str
    source_window_end: str
    strategy_model: str
    strategy_dashboard: str
    strategy_refresh: Literal["adls-scheduled"]
    strategy_as_of: str
    strategy_source: Literal[
        "strategy-mosaic-snapshot",
        "strategy-mosaic-mcp",
        "strategy-mosaic-mcp-mock",
    ]
    strategy_mcp_status: Literal["configured", "not_configured", "mock"]
    strategy_mcp_trace: StrategyMcpTrace | None = None
    totals: list[PipelineTotal]
    kpis: list[PipelineKpi]
    borough_metrics: list[BoroughMetric]
    steps: list[PipelineStep]
    limitations: list[str]


class Overview(BaseModel):
    mode: Literal["practice"]
    rule_version: str
    rule_description: str
    source_limitations: list[str]
    scenarios: list[ScenarioSummary]
    service_areas: list[str]
    data_pipeline: DataPipeline
    strategy_connection: Literal["not_configured", "snapshot", "adls_scheduled"]
    foundry_connection: Literal["not_configured", "configured"]

