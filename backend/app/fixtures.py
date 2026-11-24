import json
from pathlib import Path

from .models import BuildingSnapshot, Scenario


class ScenarioRepository:
    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path

    def load_all(self) -> list[Scenario]:
        payload = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        return [Scenario.model_validate(item) for item in payload["scenarios"]]

    def by_id(self, scenario_id: str) -> Scenario:
        matches = [scenario for scenario in self.load_all() if scenario.id == scenario_id]
        if not matches:
            raise KeyError(scenario_id)
        return matches[0]


def data_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "practice-scenarios.json"


def all_buildings(scenario: Scenario) -> list[BuildingSnapshot]:
    return scenario.buildings

