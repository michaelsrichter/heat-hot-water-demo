import os
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit, urlunsplit

import httpx
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential

from .models import Briefing, Citation, DataPipeline, ReviewRun


class BriefingProvider(Protocol):
    def create(self, run: ReviewRun, pipeline: DataPipeline) -> Briefing:
        raise NotImplementedError


class PracticeBriefingProvider:
    def create(self, run: ReviewRun, pipeline: DataPipeline) -> Briefing:
        citations = _unique_citations(run)
        needs_checking = sum(bool(item.unknowns) for item in run.items)
        metric_lines = [
            (
                f"{kpi.label}: {kpi.value:,}. "
                f"Strategy object: {kpi.strategy_object}."
            )
            for kpi in pipeline.kpis
        ]
        action_lines = [
            (
                f"{item.building_label} - {item.service_area} "
                f"({item.owner_team}): {item.action_plan[1]}"
            )
            for item in run.items
        ]
        return Briefing(
            mode="practice",
            provider="Deterministic Foundry practice agent",
            text="\n".join(
                [
                    "What Strategy Mosaic shows",
                    *[f"- {line}" for line in metric_lines],
                    "",
                    "What the practice records show",
                    (
                        f"- {run.eligible_count} synthetic building "
                        f"{'record matches' if run.eligible_count == 1 else 'records match'} "
                        "the current practice rule."
                    ),
                    (
                        f"- {needs_checking} "
                        f"{'record needs' if needs_checking == 1 else 'records need'} "
                        "more checking."
                    ),
                    "",
                    "Action plan by service area",
                    *[f"- {line}" for line in action_lines],
                    "",
                    "How staff should use this plan",
                    "- Open the cited source record and complete every verification step.",
                    "- Do not treat a closed record as proof that service was restored.",
                    "- The assigned team chooses the official action outside this demo.",
                ]
            ),
            citations=citations,
        )


@dataclass
class FoundryBriefingProvider:
    endpoint: str
    credential: TokenCredential
    client: httpx.Client

    def create(self, run: ReviewRun, pipeline: DataPipeline) -> Briefing:
        request_text = {
            "pipeline": pipeline.model_dump(mode="json"),
            "review": run.model_dump(mode="json", exclude={"briefing"}),
        }
        response = self.client.post(
            _responses_url(self.endpoint),
            headers={"Authorization": f"Bearer {self._token()}"},
            json={
                "input": (
                    "Prepare the cited HPD supervisor briefing from this governed "
                    f"Strategy Mosaic request:\n{request_text}"
                ),
                "stream": False,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return Briefing(
            mode="live",
            provider="Microsoft Foundry hosted agent",
            text=_response_text(payload),
            citations=_unique_citations(run),
        )

    def _token(self) -> str:
        return self.credential.get_token(
            os.getenv("FOUNDRY_TOKEN_SCOPE", "https://ai.azure.com/.default")
        ).token


def foundry_agent_endpoint() -> str | None:
    return os.getenv("FOUNDRY_AGENT_ENDPOINT") or os.getenv(
        "AGENT_HPD_REVIEW_AGENT_RESPONSES_ENDPOINT"
    )


def create_briefing_provider() -> BriefingProvider:
    endpoint = foundry_agent_endpoint()
    if not endpoint or os.getenv("FAKE_AI", "0") == "1":
        return PracticeBriefingProvider()
    return FoundryBriefingProvider(
        endpoint=endpoint,
        credential=DefaultAzureCredential(exclude_interactive_browser_credential=True),
        client=httpx.Client(timeout=45),
    )


def _responses_url(endpoint: str) -> str:
    parts = urlsplit(endpoint)
    if parts.path.rstrip("/").endswith("/responses"):
        return endpoint
    path = f"{parts.path.rstrip('/')}/responses"
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def _response_text(payload: dict[str, object]) -> str:
    output = payload.get("output")
    if not isinstance(output, list):
        raise ValueError("The Foundry agent returned no output array.")
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                return block["text"]
    raise ValueError("The Foundry agent returned no assistant text.")


def _unique_citations(run: ReviewRun) -> list[Citation]:
    by_url: dict[str, Citation] = {}
    for item in run.items:
        for citation in item.citations:
            by_url[citation.url] = citation
    return list(by_url.values())
