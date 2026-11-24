import json
import os
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

GUIDANCE_URL = (
    "https://www.nyc.gov/site/hpd/services-and-information/"
    "heat-and-hot-water-information.page"
)

SYSTEM_INSTRUCTIONS = f"""You are the HPD Heat and Hot Water review assistant.

Your job is to turn a governed Strategy Mosaic snapshot into a short briefing for a
New York City housing supervisor. Explain what is known, what is unknown, and what a
staff member should verify next.

Rules:
- Treat Strategy Mosaic metrics as authoritative. Never recalculate or replace them.
- Distinguish a public-record aggregate from a synthetic practice case.
- Never claim that a complaint caused a violation.
- Never claim that a closed record proves heat or hot water was restored.
- Never choose a legal or enforcement action.
- Use short sentences that a U.S. high school student can understand.
- Put evidence first, unknowns second, and a suggested staff follow-up last.
- Include the Strategy object name for every metric you mention.
- When a Strategy Mosaic MCP result is supplied in the request, use its governed metrics before
  using any snapshot values in the request. Call get_projects, get_mosaic_models
  or get_models, get_semantics, and then query.
- Use Open Complaints and Open Candidate Violations from the
  "Heat and Hot Water Review Model" for the latest dashboard totals.
- If the MCP tool is available, identify its live result separately from the
  supplied snapshot and report the query as the source of current counts.
- Group building actions by service_area and assign them to the supplied owner_team.
- Give each building a short ordered plan. Do not produce only a general summary.
- Use role-based owners, never a person's name.
- Cite only the sources supplied in the request and this official HPD guidance page:
  {GUIDANCE_URL}
"""

app = FastAPI(title="HPD Heat and Hot Water Review Agent")


def _extract_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""

    parts: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        content = item.get("content", item.get("text", ""))
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text")
                    if isinstance(text, str):
                        parts.append(text)
    return "\n".join(parts)


def _practice_briefing(request_text: str) -> str:
    return (
        "Practice briefing\n\n"
        "What the governed snapshot shows\n"
        "- The Strategy Mosaic values in the request are the source of truth.\n"
        "- Complaint rows, 311 requests, and violation records remain separate facts.\n\n"
        "What needs verification\n"
        "- Check the current source record and any missing classification or correction date.\n"
        "- A closed request or violation does not prove that heat or hot water was restored.\n\n"
        "Suggested staff follow-up\n"
        "- Compare the cited evidence with current official HPD guidance.\n"
        "- Choose the official response outside this demo.\n\n"
        "Owner routing\n"
        "- Group each building by its supplied service area and owner team.\n"
        "- Give the team a short ordered plan for that specific building.\n\n"
        f"Official HPD guidance: {GUIDANCE_URL}\n"
        f"Request summary received: {request_text[:240] or 'No detail supplied.'}"
    )


def _run_live_briefing(request_text: str) -> str:
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or os.environ.get(
        "AZURE_AI_PROJECT_ENDPOINT"
    )
    deployment = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    if not endpoint or not deployment:
        raise RuntimeError(
            "The live briefing needs FOUNDRY_PROJECT_ENDPOINT and "
            "AZURE_AI_MODEL_DEPLOYMENT_NAME."
        )

    credential = DefaultAzureCredential()
    tools: list[dict[str, Any]] = []
    toolbox_endpoint = os.getenv("TOOLBOX_ENDPOINT")
    if toolbox_endpoint:
        toolbox_token = credential.get_token("https://ai.azure.com/.default").token
        tools.append(
            {
                "type": "mcp",
                "server_label": "strategy_tools",
                "server_url": toolbox_endpoint,
                "require_approval": "never",
                "headers": {"Authorization": f"Bearer {toolbox_token}"},
            }
        )

    with AIProjectClient(endpoint=endpoint, credential=credential) as project:
        with project.get_openai_client(
            api_version=os.environ["AZURE_OPENAI_API_VERSION"]
        ) as client:
            request: dict[str, Any] = {
                "model": deployment,
                "instructions": SYSTEM_INSTRUCTIONS,
                "input": request_text,
            }
            if tools:
                request["tools"] = tools
            response = client.responses.create(**request)
    return response.output_text


def _response_payload(text: str, model: str) -> dict[str, Any]:
    response_id = f"resp_{uuid.uuid4().hex}"
    return {
        "id": response_id,
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "model": model,
        "output": [
            {
                "id": f"msg_{uuid.uuid4().hex}",
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": text,
                        "annotations": [],
                    }
                ],
            }
        ],
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        },
    }


async def _stream_payload(payload: dict[str, Any], text: str) -> AsyncIterator[str]:
    response_id = payload["id"]
    yield (
        "data: "
        + json.dumps(
            {
                "type": "response.created",
                "response": payload | {"status": "in_progress", "output": []},
            }
        )
        + "\n\n"
    )
    yield (
        "data: "
        + json.dumps(
            {
                "type": "response.output_text.delta",
                "item_id": payload["output"][0]["id"],
                "output_index": 0,
                "content_index": 0,
                "delta": text,
            }
        )
        + "\n\n"
    )
    yield (
        "data: "
        + json.dumps({"type": "response.completed", "response": payload})
        + "\n\n"
    )
    yield f"data: {{\"type\":\"done\",\"response_id\":\"{response_id}\"}}\n\n"
    yield "data: [DONE]\n\n"


@app.get("/health")
def health() -> dict[str, object]:
    fake_mode = os.getenv("FAKE_AI", "0") == "1"
    return {
        "status": "available",
        "mode": "practice" if fake_mode else "live",
        "model": os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "not_configured"),
        "strategyMcp": "configured" if os.getenv("TOOLBOX_ENDPOINT") else "not_configured",
    }


@app.get("/readiness")
def readiness() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/responses")
async def create_response(request: dict[str, Any]) -> Any:
    request_text = _extract_text(request.get("input"))
    model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "practice-briefing")
    text = (
        _practice_briefing(request_text)
        if os.getenv("FAKE_AI", "0") == "1"
        else _run_live_briefing(request_text)
    )
    payload = _response_payload(text, model)
    if request.get("stream") is True:
        return StreamingResponse(
            _stream_payload(payload, text),
            media_type="text/event-stream",
        )
    return payload


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8088")))
