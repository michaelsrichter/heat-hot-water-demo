import os
from contextlib import asynccontextmanager
from html import escape
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from .briefings import create_briefing_provider, foundry_agent_endpoint
from .fixtures import ScenarioRepository, data_path
from .models import Overview, ReviewRequest, ReviewRun, ScenarioSummary
from .pipeline import create_pipeline_manifest_provider
from .rate_limit import BoundedRateLimiter
from .services import (
    RULE_VERSION,
    ProvisionalEligibilityEvaluator,
    ReviewCoordinator,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = ScenarioRepository(data_path())
    app.state.repository = repository
    app.state.coordinator = ReviewCoordinator(repository)
    app.state.pipeline_manifest = create_pipeline_manifest_provider()
    app.state.briefing_provider = create_briefing_provider()
    yield


app = FastAPI(
    title="Heat and Hot Water Review Demo",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

allowed_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Demo-Session"],
)

run_limiter = BoundedRateLimiter(limit=6, window_seconds=60)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.get("/api/overview", response_model=Overview)
def overview(request: Request) -> Overview:
    evaluator = ProvisionalEligibilityEvaluator()
    scenarios = request.app.state.repository.load_all()
    summaries = [
        ScenarioSummary(
            id=scenario.id,
            title=scenario.title,
            kind=scenario.kind,
            source_snapshot_date=scenario.source_snapshot_date,
            simulated_review_date=scenario.simulated_review_date,
            eligible_count=sum(
                evaluator.evaluate(building, scenario.simulated_review_date)[0]
                for building in scenario.buildings
            ),
            building_count=len(scenario.buildings),
        )
        for scenario in scenarios
    ]
    pipeline = request.app.state.pipeline_manifest.load()
    strategy_connection = (
        "adls_scheduled"
        if pipeline.strategy_refresh == "adls-scheduled"
        else "snapshot"
        if pipeline.steps[5].status == "snapshot"
        else "not_configured"
    )
    service_areas = sorted(
        {
            building.service_area
            for scenario in scenarios
            for building in scenario.buildings
        }
    )
    return Overview(
        mode="practice",
        rule_version=RULE_VERSION,
        rule_description=(
            "Practice only: an approved-class heat or hot-water violation is open, "
            "its recorded correction date has passed, and the building has at least "
            "two distinct complaints in the practice window."
        ),
        source_limitations=[
            "The visible buildings and counts are synthetic. They are not HPD records.",
            "A checkpoint is not a legal deadline and urgent procedures still apply.",
            "A recorded closure does not prove that heat or hot water was restored.",
            (
                "The public aggregate snapshot refreshes daily; the visible building "
                "review records remain synthetic practice data."
            ),
        ],
        scenarios=summaries,
        service_areas=service_areas,
        data_pipeline=pipeline,
        strategy_connection=strategy_connection,
        foundry_connection=(
            "configured" if foundry_agent_endpoint() and os.getenv("FAKE_AI") != "1" else
            "not_configured"
        ),
    )


@app.post("/api/reviews/run", response_model=ReviewRun)
def run_review(payload: ReviewRequest, request: Request) -> ReviewRun:
    session_id = request.headers.get("X-Demo-Session", "")
    if len(session_id) < 24 or len(session_id) > 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A bounded browser session is required.",
        )
    rate_key = f"{request.client.host if request.client else 'unknown'}:{session_id}"
    if not run_limiter.allow(rate_key):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "The review limit was reached. Wait one minute and try again."
            },
        )
    try:
        run = request.app.state.coordinator.run(
            payload.scenario_id, payload.service_area
        )
        pipeline = request.app.state.pipeline_manifest.load()
        run.briefing = request.app.state.briefing_provider.create(run, pipeline)
        return run
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected scenario does not exist.",
        ) from error


@app.get(
    "/practice-records/{scenario_id}/{building_id}",
    response_class=HTMLResponse,
)
def practice_record(
    scenario_id: str, building_id: str, request: Request
) -> HTMLResponse:
    try:
        scenario = request.app.state.repository.by_id(scenario_id)
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected practice snapshot does not exist.",
        ) from error

    building = next(
        (
            item
            for item in scenario.buildings
            if item.building_id == building_id
        ),
        None,
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected practice building does not exist.",
        )

    violation = building.violation
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(building.label)} practice source record</title>
  <style>
    :root {{ color-scheme: light; font-family: Segoe UI, system-ui, sans-serif; }}
    body {{ margin: 0; background: #edf6fb; color: #112b3d; }}
    main {{ width: min(760px, calc(100% - 40px)); margin: 54px auto; }}
    .notice {{ padding: 10px 14px; border-radius: 999px; color: #8c4318;
      background: #fff0e3; display: inline-block; font-weight: 700; }}
    h1 {{ margin: 22px 0 10px; font-family: Georgia, serif; font-size: 2.8rem; }}
    .lead {{ color: #536b7a; font-size: 1.08rem; line-height: 1.6; }}
    dl {{ margin: 28px 0; padding: 0 24px; border: 1px solid #cbdde8;
      border-radius: 20px; background: white; }}
    dl div {{ display: grid; grid-template-columns: 210px 1fr; gap: 20px;
      padding: 16px 0; border-bottom: 1px solid #cbdde8; }}
    dl div:last-child {{ border-bottom: 0; }}
    dt {{ color: #536b7a; font-weight: 700; }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    a {{ color: #075a7c; font-weight: 700; }}
    .links {{ display: flex; gap: 18px; flex-wrap: wrap; }}
    @media (max-width: 560px) {{ dl div {{ grid-template-columns: 1fr; gap: 5px; }} }}
  </style>
</head>
<body>
  <main>
    <span class="notice">Synthetic practice record - not a real HPD case</span>
    <h1>{escape(building.label)}</h1>
    <p class="lead">
      Use this page to see the exact practice facts that were sent to Foundry.
      It does not contain resident details and is not an official city record.
    </p>
    <dl>
      <div><dt>Building ID</dt><dd>{escape(building.building_id)}</dd></div>
      <div><dt>Borough</dt><dd>{escape(building.borough)}</dd></div>
      <div><dt>Service area</dt><dd>{escape(building.service_area)}</dd></div>
      <div><dt>Responsible team</dt><dd>{escape(building.owner_team)}</dd></div>
      <div><dt>Source snapshot</dt><dd>{building.source_snapshot_date}</dd></div>
      <div><dt>Practice review date</dt><dd>{scenario.simulated_review_date}</dd></div>
      <div><dt>Distinct complaints</dt>
        <dd>{building.distinct_complaints} in {building.complaint_window_days} days</dd>
      </div>
      <div><dt>Violation ID</dt><dd>{escape(violation.violation_id)}</dd></div>
      <div><dt>Violation status</dt><dd>{escape(violation.status)}</dd></div>
      <div><dt>Recorded correction date</dt>
        <dd>{escape(str(violation.recorded_correct_by_date or "Not available"))}</dd>
      </div>
      <div><dt>Classification</dt><dd>{escape(violation.classification)}</dd></div>
    </dl>
    <div class="links">
      <a href="/#review">Return to the review</a>
      <a href="https://www.nyc.gov/site/hpd/services-and-information/heat-and-hot-water-information.page"
         target="_blank" rel="noreferrer">Read official HPD guidance</a>
    </div>
  </main>
</body>
</html>"""
    return HTMLResponse(html)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "available",
        "mode": "practice",
        "checks": {
            "practice_data": "configured",
            "strategy": "adls_scheduled",
            "foundry": (
                "configured"
                if foundry_agent_endpoint() and os.getenv("FAKE_AI") != "1"
                else "practice"
            ),
        },
        "meaning": (
            "Available for practice. A configured Foundry endpoint does not replace "
            "staff verification."
        ),
    }


static_directory = Path(os.getenv("FRONTEND_STATIC_DIR", Path(__file__).parent / "static"))
if static_directory.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=static_directory, html=True), name="frontend")

