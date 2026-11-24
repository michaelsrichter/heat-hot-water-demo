import argparse
import csv
import json
import os
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient, ContentSettings

PAGE_SIZE = 5000
SOCRATA_ROOT = "https://data.cityofnewyork.us/resource"

SOURCE_SPECS = {
    "complaint-problems.csv": {
        "dataset_id": "ygpa-z7cr",
        "title": "Housing Maintenance Code Complaints and Problems",
        "fields": [
            "received_date",
            "problem_id",
            "complaint_id",
            "building_id",
            "borough",
            "major_category",
            "minor_category",
            "problem_code",
            "complaint_status",
            "complaint_status_date",
            "problem_status",
            "problem_status_date",
            "problem_duplicate_flag",
            "unique_key",
        ],
        "where": lambda start, end: (
            f"received_date >= '{start}' and received_date < '{end}' "
            "and major_category='HEAT/HOT WATER'"
        ),
    },
    "violation-candidates.csv": {
        "dataset_id": "wvxf-dwi5",
        "title": "Housing Maintenance Code Violations",
        "fields": [
            "violationid",
            "buildingid",
            "boroid",
            "boro",
            "inspectiondate",
            "approveddate",
            "originalcorrectbydate",
            "newcorrectbydate",
            "certifieddate",
            "currentstatusid",
            "currentstatus",
            "currentstatusdate",
            "violationstatus",
            "rentimpairing",
        ],
        "where": lambda start, end: (
            f"inspectiondate >= '{start}' and inspectiondate < '{end}' "
            "and (upper(novdescription) like '%HEAT%' "
            "or upper(novdescription) like '%HOT WATER%')"
        ),
    },
    "requests-311.csv": {
        "dataset_id": "erm2-nwe9",
        "title": "311 Service Requests from 2020 to Present",
        "fields": [
            "unique_key",
            "created_date",
            "closed_date",
            "agency",
            "agency_name",
            "complaint_type",
            "descriptor",
            "status",
            "due_date",
            "borough",
            "bbl",
        ],
        "where": lambda start, end: (
            f"created_date >= '{start}' and created_date < '{end}' "
            "and agency='HPD' and complaint_type='HEAT/HOT WATER'"
        ),
    },
}

STRATEGY_FILE_PATHS = {
    "complaint-problems.csv": "strategy-complaints/complaint-problems.csv",
    "violation-candidates.csv": "strategy-violations/violation-candidates.csv",
    "requests-311.csv": "strategy-requests-311/requests-311.csv",
    "building-review.csv": "strategy-buildings/building-review.csv",
}

FORBIDDEN_FIELDS = {
    "apartment",
    "house_number",
    "street_name",
    "incident_address",
    "resolution_description",
    "latitude",
    "longitude",
    "location",
}


def fetch_source(specification: dict, start: str, end: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    offset = 0
    while True:
        query = urlencode(
            {
                "$select": ",".join(specification["fields"]),
                "$where": specification["where"](start, end),
                "$limit": PAGE_SIZE,
                "$offset": offset,
                "$order": ":id",
            }
        )
        request = Request(  # noqa: S310
            f"{SOCRATA_ROOT}/{specification['dataset_id']}.json?{query}",
            headers={"Accept": "application/json", "User-Agent": "HeatHotWaterADLSDemo/0.1"},
        )
        with urlopen(request, timeout=90) as response:  # noqa: S310
            page = json.load(response)
        if not isinstance(page, list):
            raise RuntimeError(f"Unexpected source payload for {specification['dataset_id']}.")
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def allowed_row(row: dict[str, str], fields: list[str]) -> dict[str, str]:
    return {field: row.get(field, "") for field in fields}


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, str]]) -> None:
    forbidden = set(fields) & FORBIDDEN_FIELDS
    if forbidden:
        raise ValueError(f"Forbidden fields cannot be exported: {sorted(forbidden)}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(allowed_row(row, fields))


def build_building_rows(
    complaints: list[dict[str, str]],
    violations: list[dict[str, str]],
    start: str,
    end: str,
) -> list[dict[str, object]]:
    complaint_by_id: dict[str, dict[str, str]] = {}
    for row in complaints:
        complaint_id = row.get("complaint_id", "")
        if complaint_id:
            complaint_by_id[complaint_id] = row

    complaint_by_building: dict[str, dict[str, object]] = {}
    for row in complaint_by_id.values():
        building_id = row.get("building_id", "")
        if not building_id:
            continue
        summary = complaint_by_building.setdefault(
            building_id,
            {
                "borough": row.get("borough", ""),
                "complaints": 0,
                "open_complaints": 0,
                "latest_complaint_date": "",
            },
        )
        summary["complaints"] = int(summary["complaints"]) + 1
        if (row.get("complaint_status") or "").strip().upper() == "OPEN":
            summary["open_complaints"] = int(summary["open_complaints"]) + 1
        received_date = row.get("received_date", "")
        if received_date > str(summary["latest_complaint_date"]):
            summary["latest_complaint_date"] = received_date

    violation_by_id: dict[str, dict[str, str]] = {}
    for row in violations:
        violation_id = row.get("violationid", "")
        if violation_id:
            violation_by_id[violation_id] = row

    violation_by_building: dict[str, dict[str, object]] = {}
    for row in violation_by_id.values():
        building_id = row.get("buildingid", "")
        if not building_id:
            continue
        summary = violation_by_building.setdefault(
            building_id,
            {
                "candidate_violation_count": 0,
                "open_candidate_violation_count": 0,
                "statuses": set(),
                "latest_violation_status_date": "",
                "latest_original_correct_by_date": "",
                "latest_new_correct_by_date": "",
            },
        )
        summary["candidate_violation_count"] = (
            int(summary["candidate_violation_count"]) + 1
        )
        if (row.get("violationstatus") or "").strip().lower() == "open":
            summary["open_candidate_violation_count"] = (
                int(summary["open_candidate_violation_count"]) + 1
            )
        statuses = summary["statuses"]
        if isinstance(statuses, set) and row.get("currentstatus"):
            statuses.add(row["currentstatus"])
        for output_name, source_name in (
            ("latest_violation_status_date", "currentstatusdate"),
            ("latest_original_correct_by_date", "originalcorrectbydate"),
            ("latest_new_correct_by_date", "newcorrectbydate"),
        ):
            value = row.get(source_name, "")
            if value > str(summary[output_name]):
                summary[output_name] = value

    result: list[dict[str, object]] = []
    for building_id in sorted(complaint_by_building):
        complaint = complaint_by_building[building_id]
        violation = violation_by_building.get(building_id, {})
        statuses = violation.get("statuses", set())
        result.append(
            {
                "source_snapshot_start": start,
                "source_snapshot_end": end,
                "building_id": building_id,
                "borough": complaint["borough"],
                "distinct_complaints": complaint["complaints"],
                "open_complaint_count": complaint["open_complaints"],
                "latest_complaint_date": complaint["latest_complaint_date"],
                "candidate_violation_count": violation.get(
                    "candidate_violation_count", 0
                ),
                "open_candidate_violation_count": violation.get(
                    "open_candidate_violation_count", 0
                ),
                "observed_statuses": "|".join(sorted(statuses)),
                "latest_violation_status_date": violation.get(
                    "latest_violation_status_date", ""
                ),
                "latest_original_correct_by_date": violation.get(
                    "latest_original_correct_by_date", ""
                ),
                "latest_new_correct_by_date": violation.get(
                    "latest_new_correct_by_date", ""
                ),
                "classification_status": "needs_review",
                "review_state": "needs_verification",
                "provisional_eligible": 0,
                "rule_version": "adls-strategy-0.1",
            }
        )
    return result


BUILDING_FIELDS = [
    "source_snapshot_start",
    "source_snapshot_end",
    "building_id",
    "borough",
    "distinct_complaints",
    "open_complaint_count",
    "latest_complaint_date",
    "candidate_violation_count",
    "open_candidate_violation_count",
    "observed_statuses",
    "latest_violation_status_date",
    "latest_original_correct_by_date",
    "latest_new_correct_by_date",
    "classification_status",
    "review_state",
    "provisional_eligible",
    "rule_version",
]


def build_manifest(
    account_url: str,
    container: str,
    start: str,
    end: str,
    source_counts: dict[str, int],
    building_count: int,
    kpis: list[dict[str, object]],
    loaded_at: str,
    borough_metrics: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "architecture": (
            "NYC Open Data -> Azure ingestion -> ADLS Gen2 -> Strategy Mosaic -> "
            "dashboard and review app"
        ),
        "mode": "adls-gen2-strategy",
        "storage_account": "managed-by-deployment",
        "container": container,
        "manifest_path": "current/manifest.json",
        "source_window_start": start,
        "source_window_end": end,
        "strategy_model": "Heat and Hot Water Review Model",
        "strategy_dashboard": "Heat and Hot Water Review Dashboard",
        "strategy_refresh": "adls-scheduled",
        "strategy_as_of": end.split("T")[0],
        "strategy_source": "strategy-mosaic-snapshot",
        "strategy_mcp_status": "not_configured",
        "totals": [
            {"label": "Source rows", "value": sum(source_counts.values())},
            {"label": "Building rows", "value": building_count},
            {"label": "Distinct source files", "value": len(source_counts)},
        ],
        "kpis": kpis,
        "borough_metrics": borough_metrics or [],
        "steps": [
            {
                "order": 1,
                "id": "public-data",
                "title": "Read NYC HPD records",
                "owner": "NYC Open Data",
                "detail": (
                    "Read heat and hot-water complaints, candidate violations, "
                    "and 311 requests."
                ),
                "status": "ready",
                "artifact": loaded_at,
            },
            {
                "order": 2,
                "id": "prepare",
                "title": "Count the right thing",
                "owner": "Azure ingestion job",
                "detail": (
                    "Count distinct complaints, keep source grains separate, "
                    "and remove personal fields."
                ),
                "status": "ready",
                "artifact": "current/*.csv",
            },
            {
                "order": 3,
                "id": "store",
                "title": "Save a dated copy",
                "owner": "Azure",
                "detail": "Keep stable Strategy files and a dated archive in ADLS Gen2.",
                "status": "ready",
                "artifact": f"adls://{container}/current/",
            },
            {
                "order": 4,
                "id": "connect",
                "title": "Define the facts in Strategy",
                "owner": "Strategy Mosaic",
                "detail": (
                    "Use one shared definition for each KPI, building relationship, "
                    "date, and rule version."
                ),
                "status": "configured",
                "artifact": "Heat and Hot Water Review Model",
            },
            {
                "order": 5,
                "id": "model",
                "title": "Show the same numbers",
                "owner": "Strategy dashboard",
                "detail": "Use the Mosaic measures in the dashboard and review workflow.",
                "status": "configured",
                "artifact": "Heat and Hot Water Review Dashboard",
            },
            {
                "order": 6,
                "id": "briefing",
                "title": "Prepare a cited briefing",
                "owner": "Foundry IQ",
                "detail": (
                    "Read the governed facts and approved HPD guidance, "
                    "then draft a review-ready summary."
                ),
                "status": "configured",
                "artifact": "HPD Review Agent",
            },
            {
                "order": 7,
                "id": "present",
                "title": "Let an HPD official review",
                "owner": "Housing staff",
                "detail": (
                    "Check the facts, missing details, guidance, and suggested "
                    "next step before acting."
                ),
                "status": "configured",
                "artifact": "Case review list",
            },
        ],
        "limitations": [
            "The deployment uses managed identity and never publishes storage credentials.",
            "Candidate heat classifications remain needs_review.",
            "Apartment, address, person, location, and source free-text fields are excluded.",
        ],
    }


def build_strategy_kpis(
    building_rows: list[dict[str, object]],
    complaint_rows: list[dict[str, str]],
    violation_rows: list[dict[str, str]],
    request_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    distinct_complaints = sum(int(row["distinct_complaints"]) for row in building_rows)
    candidate_violations = sum(
        int(row["candidate_violation_count"]) for row in building_rows
    )
    buildings_with_candidates = sum(
        int(row["candidate_violation_count"]) > 0 for row in building_rows
    )
    unresolved_complaints = len(
        {
            row["complaint_id"]
            for row in complaint_rows
            if row.get("complaint_id")
            and (row.get("complaint_status") or "").strip().upper() == "OPEN"
        }
    )
    unresolved_candidate_violations = len(
        {
            row["violationid"]
            for row in violation_rows
            if row.get("violationid")
            and (row.get("violationstatus") or "").strip().lower() == "open"
        }
    )
    return [
        {
            "id": "unresolved-complaints",
            "label": "Unresolved heat or hot-water complaints",
            "value": unresolved_complaints,
            "unit": "complaints",
            "definition": (
                "Distinct complaint IDs whose latest complaint_status is OPEN in "
                "the Strategy source snapshot."
            ),
            "why_it_matters": (
                "Shows the main complaint queue for supervisors to review now."
            ),
            "strategy_object": "Open Complaints",
        },
        {
            "id": "unresolved-candidate-violations",
            "label": "Unresolved candidate violations",
            "value": unresolved_candidate_violations,
            "unit": "violations",
            "definition": (
                "Distinct candidate violation IDs whose violationstatus is Open. "
                "The heat classification still needs review."
            ),
            "why_it_matters": (
                "Shows possible enforcement records that may need staff verification."
            ),
            "strategy_object": "Open Candidate Violations",
        },
        {
            "id": "buildings-with-complaints",
            "label": "Buildings with heat or hot-water reports",
            "value": len(building_rows),
            "unit": "buildings",
            "definition": (
                "Distinct HPD building IDs with at least one approved heat or "
                "hot-water complaint category in the source window."
            ),
            "why_it_matters": (
                "Shows the number of buildings an HPD supervisor may need to review."
            ),
            "strategy_object": "Building (merged across sources)",
        },
        {
            "id": "distinct-complaints",
            "label": "Distinct heat or hot-water complaints",
            "value": distinct_complaints,
            "unit": "complaints",
            "definition": (
                "Distinct complaint_id values. Problem rows are not counted as "
                "separate complaints."
            ),
            "why_it_matters": (
                "Prevents one complaint with several problem rows from being counted "
                "more than once."
            ),
            "strategy_object": "Distinct Complaints",
        },
        {
            "id": "candidate-violations",
            "label": "Candidate violation records",
            "value": candidate_violations,
            "unit": "candidate violations",
            "definition": (
                "Distinct violation IDs found by the provisional heat or hot-water "
                "text screen and linked at building level."
            ),
            "why_it_matters": (
                "Flags building histories for review without claiming that a "
                "particular complaint caused a violation."
            ),
            "strategy_object": "Candidate Violation Count",
        },
        {
            "id": "buildings-with-candidate-violations",
            "label": "Buildings with a candidate violation",
            "value": buildings_with_candidates,
            "unit": "buildings",
            "definition": (
                "Buildings in the complaint summary with at least one candidate "
                "violation record."
            ),
            "why_it_matters": (
                "Narrows the review set while preserving buildings with no matching "
                "violation."
            ),
            "strategy_object": "Building → Candidate Violation Count",
        },
        {
            "id": "supporting-311-requests",
            "label": "Supporting 311 requests",
            "value": len(request_rows),
            "unit": "requests",
            "definition": (
                "HPD heat or hot-water 311 requests in the source window. These remain "
                "supporting context until the linkage is validated."
            ),
            "why_it_matters": (
                "Shows when requests were made without treating a closed request as "
                "proof that heat or hot water was restored."
            ),
            "strategy_object": "Request Unique Key",
        },
        {
            "id": "raw-problem-rows",
            "label": "Problem rows checked",
            "value": len(complaint_rows),
            "unit": "problem rows",
            "definition": (
                "Raw HPD problem rows read during ingestion. This is not the complaint "
                "count."
            ),
            "why_it_matters": (
                "Makes the difference between source rows and distinct complaints "
                "visible."
            ),
            "strategy_object": "Problem",
        },
    ]


def build_borough_metrics(
    building_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    by_borough: dict[str, dict[str, int]] = {}
    for row in building_rows:
        borough = str(row.get("borough", "")).title()
        totals = by_borough.setdefault(
            borough,
            {
                "distinct_complaints": 0,
                "candidate_violations": 0,
                "unresolved_complaints": 0,
                "unresolved_candidate_violations": 0,
            },
        )
        totals["distinct_complaints"] += int(row.get("distinct_complaints", 0))
        totals["candidate_violations"] += int(
            row.get("candidate_violation_count", 0)
        )
        totals["unresolved_complaints"] += int(row.get("open_complaint_count", 0))
        totals["unresolved_candidate_violations"] += int(
            row.get("open_candidate_violation_count", 0)
        )

    return [
        {
            "borough": borough,
            **totals,
        }
        for borough, totals in sorted(by_borough.items())
    ]


def upload_file(
    credential: DefaultAzureCredential,
    account_url: str,
    container: str,
    blob_path: str,
    local_path: Path,
) -> None:
    client = BlobClient(
        account_url=account_url,
        container_name=container,
        blob_name=blob_path,
        credential=credential,
    )
    content_type = (
        "application/json" if local_path.suffix == ".json" else "text/csv"
    )
    with local_path.open("rb") as data:
        client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )


def run(
    start: str, end: str, output_dir: Path
) -> tuple[
    dict[str, Path],
    dict[str, int],
    dict[str, list[dict[str, str]]],
    list[dict[str, object]],
]:
    source_rows: dict[str, list[dict[str, str]]] = {}
    source_counts: dict[str, int] = {}
    paths: dict[str, Path] = {}
    for filename, specification in SOURCE_SPECS.items():
        rows = fetch_source(specification, start, end)
        source_rows[filename] = rows
        source_counts[filename] = len(rows)
        path = output_dir / filename
        write_csv(path, specification["fields"], rows)
        paths[filename] = path

    building_rows = build_building_rows(
        source_rows["complaint-problems.csv"],
        source_rows["violation-candidates.csv"],
        start,
        end,
    )
    building_path = output_dir / "building-review.csv"
    write_csv(building_path, BUILDING_FIELDS, building_rows)
    paths["building-review.csv"] = building_path
    return (
        paths,
        {**source_counts, "building-review.csv": len(building_rows)},
        source_rows,
        building_rows,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window-start", default="2026-11-01T00:00:00")
    parser.add_argument(
        "--window-end",
        default=f"{datetime.now(UTC).date().isoformat()}T00:00:00",
    )
    parser.add_argument("--account-url", default=os.getenv("ADLS_ACCOUNT_URL"))
    parser.add_argument("--container", default=os.getenv("ADLS_CONTAINER", "heat-hot-water"))
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args()

    with TemporaryDirectory(prefix="hhw-adls-") as directory:
        output_dir = Path(directory)
        paths, counts, source_rows, building_rows = run(
            args.window_start, args.window_end, output_dir
        )
        loaded_at = datetime.now(UTC).isoformat()
        if args.local_only:
            account_url = args.account_url or "https://not-deployed.blob.core.windows.net"
        elif not args.account_url:
            raise RuntimeError(
                "Set ADLS_ACCOUNT_URL or pass --account-url. "
                "Use --local-only to generate files without uploading."
            )
        else:
            account_url = args.account_url

        source_counts = {key: value for key, value in counts.items() if key in SOURCE_SPECS}
        manifest = build_manifest(
            account_url=account_url,
            container=args.container,
            start=args.window_start,
            end=args.window_end,
            source_counts=source_counts,
            building_count=counts["building-review.csv"],
            kpis=build_strategy_kpis(
                building_rows=building_rows,
                complaint_rows=source_rows["complaint-problems.csv"],
                violation_rows=source_rows["violation-candidates.csv"],
                request_rows=source_rows["requests-311.csv"],
            ),
            loaded_at=loaded_at,
            borough_metrics=build_borough_metrics(building_rows),
        )
        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        paths["manifest.json"] = manifest_path

        if not args.local_only:
            credential = DefaultAzureCredential(
                exclude_interactive_browser_credential=True
            )
            snapshot = args.window_end[:10]
            for filename, local_path in paths.items():
                upload_file(
                    credential,
                    account_url,
                    args.container,
                    f"current/{filename}",
                    local_path,
                )
                upload_file(
                    credential,
                    account_url,
                    args.container,
                    f"archive/{snapshot}/{filename}",
                    local_path,
                )
                strategy_path = STRATEGY_FILE_PATHS.get(filename)
                if strategy_path:
                    upload_file(
                        credential,
                        account_url,
                        args.container,
                        strategy_path,
                        local_path,
                    )

        print(json.dumps({"counts": counts, "manifest": manifest}, indent=2))


if __name__ == "__main__":
    main()
