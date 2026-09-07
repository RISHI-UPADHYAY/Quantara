from __future__ import annotations

from app.services.analysis.scenario.scenario_definition import ScenarioDefinition


class ScenarioRegistry:
    """
    Registry of predefined stress scenarios.
    """

    _SCENARIOS: dict[str, ScenarioDefinition] = {
        "technology_selloff": ScenarioDefinition(
            name="Technology Selloff",
            scenario_type="deterministic_price_shock",
            description=(
                "Stress scenario representing a broad technology-sector selloff."
            ),
            shocks= {
                "AAPL": -0.10,
                "MSFT": -0.15,
                "NVDA": -0.25,
            },
        ),
    }


    @classmethod
    def get(
        cls,
        scenario_id: str,
    ) -> ScenarioDefinition:
        normalized_id = scenario_id.strip().lower()

        try:
            return cls._SCENARIOS[normalized_id]

        except KeyError as exc:
            raise ValueError(
                f"Unknown scenario: {scenario_id}"
            )from exc


    @classmethod
    def exists(
        cls,
        scenario_id: str,
    ) -> bool:
        normalized_id = scenario_id.strip().lower()

        return normalized_id in cls._SCENARIOS


    @classmethod
    def list_scenarios(cls) -> list[ScenarioDefinition]:

        return list(cls._SCENARIOS.values())


    @classmethod
    def list_ids(cls) -> list[str]:

        return list(cls._SCENARIOS.keys())