from app.ingest_adls import (
    FORBIDDEN_FIELDS,
    SOURCE_SPECS,
    STRATEGY_FILE_PATHS,
    build_borough_metrics,
    build_building_rows,
    build_manifest,
    build_strategy_kpis,
)
from app.pipeline import (
    LocalPipelineManifestProvider,
    StrategyMcpMockManifestProvider,
    pipeline_manifest_path,
    strategy_mcp_mock_path,
)


def test_source_contract_excludes_personal_and_free_text_fields() -> None:
    exported_fields = {
        field
        for specification in SOURCE_SPECS.values()
        for field in specification["fields"]
    }

    assert not (exported_fields & FORBIDDEN_FIELDS)


def test_strategy_storage_folders_are_one_file_per_table() -> None:
    folders = [path.rsplit("/", 1)[0] for path in STRATEGY_FILE_PATHS.values()]

    assert len(folders) == len(set(folders))
    assert set(folders) == {
        "strategy-complaints",
        "strategy-violations",
        "strategy-requests-311",
        "strategy-buildings",
    }


def test_building_summary_uses_distinct_complaints_and_preserves_candidate_status() -> None:
    complaints = [
        {
            "complaint_id": "C-1",
            "building_id": "B-1",
            "borough": "BRONX",
            "complaint_status": "OPEN",
            "received_date": "2026-11-02T12:00:00",
        },
        {
            "complaint_id": "C-1",
            "building_id": "B-1",
            "borough": "BRONX",
            "complaint_status": "OPEN",
            "received_date": "2026-11-02T12:00:00",
        },
        {
            "complaint_id": "C-2",
            "building_id": "B-1",
            "borough": "BRONX",
            "complaint_status": "OPEN",
            "received_date": "2026-11-03T12:00:00",
        },
    ]
    violations = [
        {
            "violationid": "V-1",
            "buildingid": "B-1",
            "currentstatus": "VIOLATION OPEN",
            "currentstatusdate": "2026-11-04",
            "violationstatus": "Open",
            "originalcorrectbydate": "2026-11-05",
            "newcorrectbydate": "",
        }
    ]

    rows = build_building_rows(
        complaints,
        violations,
        "2026-11-01T00:00:00",
        "2026-11-19T00:00:00",
    )

    assert len(rows) == 1
    assert rows[0]["distinct_complaints"] == 2
    assert rows[0]["open_complaint_count"] == 2
    assert rows[0]["candidate_violation_count"] == 1
    assert rows[0]["open_candidate_violation_count"] == 1
    assert rows[0]["observed_statuses"] == "VIOLATION OPEN"
    assert rows[0]["review_state"] == "needs_verification"


def test_manifest_names_the_adls_to_strategy_process() -> None:
    manifest = build_manifest(
        "https://example.blob.core.windows.net",
        "heat-hot-water",
        "2026-11-01T00:00:00",
        "2026-11-19T00:00:00",
        {
            "complaint-problems.csv": 2,
            "violation-candidates.csv": 1,
            "requests-311.csv": 3,
        },
        building_count=1,
        kpis=[
            {
                "id": "buildings-with-complaints",
                "label": "Buildings with reports",
                "value": 1,
                "unit": "buildings",
                "definition": "Distinct buildings in the source window.",
                "why_it_matters": "Defines the review population.",
                "strategy_object": "Building",
            }
        ],
        loaded_at="2026-11-19T00:00:00+00:00",
    )

    assert manifest["mode"] == "adls-gen2-strategy"
    assert [step["order"] for step in manifest["steps"]] == [1, 2, 3, 4, 5, 6, 7]
    assert manifest["steps"][3]["status"] == "configured"
    assert manifest["steps"][5]["status"] == "configured"
    assert manifest["strategy_source"] == "strategy-mosaic-snapshot"
    assert manifest["strategy_mcp_status"] == "not_configured"
    assert "ADLS Gen2" in manifest["architecture"]


def test_strategy_kpis_count_unresolved_complaints_and_violations() -> None:
    kpis = build_strategy_kpis(
        building_rows=[
            {
                "distinct_complaints": 2,
                "candidate_violation_count": 1,
            }
        ],
        complaint_rows=[
            {
                "complaint_id": "C-1",
                "complaint_status": "OPEN",
                "borough": "BRONX",
            },
            {
                "complaint_id": "C-1",
                "complaint_status": "OPEN",
                "borough": "BRONX",
            },
            {
                "complaint_id": "C-2",
                "complaint_status": "CLOSE",
                "borough": "BRONX",
            },
        ],
        violation_rows=[
            {
                "violationid": "V-1",
                "violationstatus": "Open",
                "boro": "BRONX",
            }
        ],
        request_rows=[],
    )

    by_id = {kpi["id"]: kpi for kpi in kpis}
    assert by_id["unresolved-complaints"]["value"] == 1
    assert by_id["unresolved-candidate-violations"]["value"] == 1


def test_borough_metrics_keep_open_work_at_distinct_record_grain() -> None:
    metrics = build_borough_metrics(
        [
            {
                "building_id": "B-1",
                "borough": "BRONX",
                "distinct_complaints": 2,
                "candidate_violation_count": 1,
                "open_complaint_count": 1,
                "open_candidate_violation_count": 1,
            },
        ],
    )

    assert metrics == [
        {
            "borough": "Bronx",
            "distinct_complaints": 2,
            "candidate_violations": 1,
            "unresolved_complaints": 1,
            "unresolved_candidate_violations": 1,
        }
    ]


def test_local_process_manifest_matches_api_contract() -> None:
    manifest = LocalPipelineManifestProvider(pipeline_manifest_path()).load()

    assert manifest.mode == "adls-gen2-strategy"
    assert len(manifest.steps) == 7
    assert len(manifest.kpis) == 8
    assert manifest.kpis[0].id == "unresolved-complaints"
    assert manifest.borough_metrics[0].borough == "Bronx"


def test_mock_strategy_mcp_provider_preserves_governed_values_and_labels_mode() -> None:
    base = LocalPipelineManifestProvider(pipeline_manifest_path())
    manifest = StrategyMcpMockManifestProvider(base, strategy_mcp_mock_path()).load()

    assert manifest.strategy_source == "strategy-mosaic-mcp-mock"
    assert manifest.strategy_mcp_status == "mock"
    assert manifest.strategy_mcp_trace is not None
    assert manifest.strategy_mcp_trace.mode == "mock"
    assert [step.tool for step in manifest.strategy_mcp_trace.trace] == [
        "strategy-mosaic-mcp___get_projects",
        "strategy-mosaic-mcp___get_models",
        "strategy-mosaic-mcp___get_semantics",
        "strategy-mosaic-mcp___query",
    ]
    assert manifest.kpis == base.load().kpis
    assert manifest.totals[0].value == 66517

