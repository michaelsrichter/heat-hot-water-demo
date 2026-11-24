from abc import ABC, abstractmethod
from datetime import UTC, date, datetime

from .fixtures import ScenarioRepository
from .models import BuildingSnapshot, Citation, ReviewItem, ReviewRun, Scenario

RULE_VERSION = "practice-0.1"


class EligibilityEvaluator(ABC):
    @abstractmethod
    def evaluate(self, building: BuildingSnapshot, review_date: date) -> tuple[bool, str]:
        raise NotImplementedError


class ProvisionalEligibilityEvaluator(EligibilityEvaluator):
    minimum_complaints = 2

    def evaluate(self, building: BuildingSnapshot, review_date: date) -> tuple[bool, str]:
        violation = building.violation
        if (
            violation.classification != "approved_heat_or_hot_water"
            or violation.status == "unknown"
            or violation.recorded_correct_by_date is None
        ):
            return False, "A required field or approved classification is missing."
        eligible = (
            violation.status == "open"
            and violation.recorded_correct_by_date < review_date
            and building.distinct_complaints >= self.minimum_complaints
        )
        if eligible:
            return True, (
                f"The recorded correction date passed and the building has "
                f"{building.distinct_complaints} distinct complaints."
            )
        if violation.status == "closed":
            return False, "The violation was recorded as closed in this snapshot."
        if violation.recorded_correct_by_date >= review_date:
            return False, "The recorded correction date has not passed in this scenario."
        return False, "The practice repeat-complaint minimum was not reached."


class ReviewItemBuilder:
    def __init__(self, evaluator: EligibilityEvaluator) -> None:
        self._evaluator = evaluator

    def build(self, scenario: Scenario, previously_eligible: set[str]) -> list[ReviewItem]:
        items: list[ReviewItem] = []
        for building in scenario.buildings:
            eligible, trigger = self._evaluator.evaluate(
                building, scenario.simulated_review_date
            )
            violation = building.violation
            needs_verification = (
                violation.status == "unknown"
                or violation.recorded_correct_by_date is None
                or violation.classification != "approved_heat_or_hot_water"
            )
            if not eligible and not needs_verification:
                continue

            if needs_verification:
                state = "needs_verification"
            elif building.building_id in previously_eligible:
                state = "carried_forward"
            else:
                state = "new"

            unknowns = []
            if violation.status == "unknown":
                unknowns.append("The violation status is unknown in this snapshot.")
            if violation.recorded_correct_by_date is None:
                unknowns.append("A usable recorded correction date is missing.")
            if violation.classification != "approved_heat_or_hot_water":
                unknowns.append("The heat and hot-water classification needs review.")

            if needs_verification:
                action_plan = [
                    f"Assign this record to the {building.owner_team}.",
                    (
                        "Open the current source record and fill the missing or uncertain "
                        "violation fields."
                    ),
                    (
                        "Compare the result with the official HPD heat and hot-water "
                        "guidance before choosing a response."
                    ),
                ]
            else:
                action_plan = [
                    f"Assign this record to the {building.owner_team}.",
                    (
                        "Confirm that the violation is still open and that the recorded "
                        "correction date has passed."
                    ),
                    (
                        f"Review the {building.distinct_complaints} distinct complaints "
                        "and the current source evidence."
                    ),
                    "Document the official follow-up outside this demo.",
                ]

            items.append(
                ReviewItem(
                    building_id=building.building_id,
                    building_label=building.label,
                    borough=building.borough,
                    service_area=building.service_area,
                    owner_team=building.owner_team,
                    state=state,
                    trigger=trigger,
                    rule_version=RULE_VERSION,
                    observed_facts=[
                        f"Violation {violation.violation_id} is recorded as {violation.status}.",
                        (
                            f"The recorded correction date is "
                            f"{violation.recorded_correct_by_date or 'not available'}."
                        ),
                        (
                            f"{building.distinct_complaints} distinct complaints appear "
                            f"inside the {building.complaint_window_days}-day window."
                        ),
                    ],
                    unknowns=unknowns,
                    suggested_follow_up=(
                        f"The {building.owner_team} can verify the cited records and "
                        "current official guidance before choosing a follow-up."
                    ),
                    action_plan=action_plan,
                    source_snapshot_date=scenario.source_snapshot_date,
                    simulated_review_date=scenario.simulated_review_date,
                    citations=[
                        Citation(
                            title="Practice building record",
                            url=(
                                f"/practice-records/{scenario.id}/"
                                f"{building.building_id}"
                            ),
                            scope="data",
                            passage="Synthetic record for the selected source snapshot.",
                        ),
                        Citation(
                            title="HPD heat and hot water information",
                            url=(
                                "https://www.nyc.gov/site/hpd/"
                                "services-and-information/heat-and-hot-water-information.page"
                            ),
                            scope="guidance",
                            passage=(
                                "Use the current HPD page for official heat and hot-water "
                                "requirements. This demo does not restate a legal deadline."
                            ),
                        ),
                    ],
                )
            )
        return items


class ReviewCoordinator:
    def __init__(self, repository: ScenarioRepository) -> None:
        self._repository = repository
        self._evaluator = ProvisionalEligibilityEvaluator()
        self._builder = ReviewItemBuilder(self._evaluator)

    @staticmethod
    def _strategy_count(scenario: Scenario, evaluator: EligibilityEvaluator) -> int:
        return sum(
            1
            for building in scenario.buildings
            if evaluator.evaluate(building, scenario.simulated_review_date)[0]
        )

    def run(self, scenario_id: str, service_area: str | None = None) -> ReviewRun:
        scenario = self._repository.by_id(scenario_id)
        if service_area:
            scenario = scenario.model_copy(
                update={
                    "buildings": [
                        building
                        for building in scenario.buildings
                        if building.service_area == service_area
                    ]
                }
            )
        all_scenarios = self._repository.load_all()
        previous_dates = [
            item
            for item in all_scenarios
            if item.simulated_review_date < scenario.simulated_review_date
        ]
        previously_eligible: set[str] = set()
        for previous in previous_dates:
            for building in previous.buildings:
                if service_area and building.service_area != service_area:
                    continue
                eligible, _ = self._evaluator.evaluate(
                    building, previous.simulated_review_date
                )
                if eligible:
                    previously_eligible.add(building.building_id)

        started_at = datetime.now(UTC)
        items = self._builder.build(scenario, previously_eligible)
        eligible_count = sum(item.state in {"new", "carried_forward"} for item in items)
        strategy_count = self._strategy_count(scenario, self._evaluator)
        return ReviewRun(
            scenario_id=scenario.id,
            mode="practice",
            started_at=started_at.isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
            rule_version=RULE_VERSION,
            steps=[
                "Checked the saved source snapshot.",
                "Applied the same provisional rule used by the practice dashboard.",
                "Retrieved the approved practice guidance links.",
                "Grouped buildings by borough and neighborhood service area.",
                "Prepared owner-ready actions for the review items.",
                (
                    f"Reconciled {eligible_count} worklist "
                    f"{'record' if eligible_count == 1 else 'records'} with "
                    f"{strategy_count} Strategy "
                    f"{'record' if strategy_count == 1 else 'records'}."
                ),
            ],
            eligible_count=eligible_count,
            strategy_count=strategy_count,
            items=items,
        )

