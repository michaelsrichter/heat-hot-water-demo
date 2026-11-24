import json
import os
from pathlib import Path
from typing import Protocol

from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient

from .models import DataPipeline, StrategyMcpTrace


class PipelineManifestProvider(Protocol):
    def load(self) -> DataPipeline:
        raise NotImplementedError


class LocalPipelineManifestProvider:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> DataPipeline:
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        return DataPipeline.model_validate(payload)


class AdlsPipelineManifestProvider:
    def __init__(self, account_url: str, container: str, path: str) -> None:
        self._client = BlobClient(
            account_url=account_url,
            container_name=container,
            blob_name=path,
            credential=DefaultAzureCredential(exclude_interactive_browser_credential=True),
        )

    def load(self) -> DataPipeline:
        try:
            downloaded = self._client.download_blob()
            payload = json.loads(downloaded.readall())
        except (AzureError, json.JSONDecodeError) as error:
            raise RuntimeError(
                "The ADLS pipeline manifest is not readable. "
                "Check the account, container, path, and app storage data role."
            ) from error
        return DataPipeline.model_validate(payload)


class StrategyMcpMockManifestProvider:
    def __init__(self, provider: PipelineManifestProvider, mock_path: Path) -> None:
        self._provider = provider
        self._mock_path = mock_path

    def load(self) -> DataPipeline:
        pipeline = self._provider.load()
        trace = StrategyMcpTrace.model_validate(
            json.loads(self._mock_path.read_text(encoding="utf-8"))
        )
        return pipeline.model_copy(
            update={
                "strategy_source": "strategy-mosaic-mcp-mock",
                "strategy_mcp_status": "mock",
                "strategy_mcp_trace": trace,
            }
        )


def pipeline_manifest_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "pipeline-status.json"


def strategy_mcp_mock_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "strategy-mcp-mock.json"


def create_pipeline_manifest_provider() -> PipelineManifestProvider:
    account_url = os.getenv("ADLS_ACCOUNT_URL")
    if not account_url:
        provider: PipelineManifestProvider = LocalPipelineManifestProvider(
            pipeline_manifest_path()
        )
    else:
        provider = AdlsPipelineManifestProvider(
            account_url=account_url,
            container=os.environ["ADLS_CONTAINER"],
            path=os.getenv("ADLS_MANIFEST_PATH", "current/manifest.json"),
        )
    if os.getenv("STRATEGY_MCP_MODE", "snapshot") == "mock":
        return StrategyMcpMockManifestProvider(provider, strategy_mcp_mock_path())
    return provider
