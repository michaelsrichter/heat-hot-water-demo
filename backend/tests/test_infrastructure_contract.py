from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_public_infrastructure_has_no_policy_bypass_job() -> None:
    assert not (ROOT / "infra" / "tag-maintenance-job.bicep").exists()

    template = (ROOT / "infra" / "main.bicep").read_text(encoding="utf-8")
    assert "securitycontrol" not in template


def test_storage_authentication_uses_managed_identity_only() -> None:
    template = (ROOT / "infra" / "resources.bicep").read_text(encoding="utf-8")

    assert "allowSharedKeyAccess: false" in template
    assert "allowBlobPublicAccess: false" in template
    assert "supportsHttpsTrafficOnly: true" in template
    assert "connectorKeyVault" not in template
    assert not (ROOT / "infra" / "key-vault.bicep").exists()
