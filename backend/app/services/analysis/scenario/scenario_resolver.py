from __future__ import annotations

from typing import Any

from app.services.analysis.scenario.scenario_definition import ScenarioDefinition
from app.services.analysis.scenario.scenario_registry import ScenarioRegistry


class ScenarioResolver:
    """
    Resolves scenario identifiers into executable scenario definitions.
    """

    @staticmethod
    def resolve(
        scenario_id: str,
    ) -> ScenarioDefinition:

        return ScenarioRegistry.get(scenario_id)


    @staticmethod
    def resolve_shocks(
        scenario_id: str,
    ) -> dict[str, float]:
        scenario = ScenarioResolver.resolve(scenario_id)

        return {
            str(symbol): float(shock)
            for symbol, shock in scenario.shocks.items()
        }


    @staticmethod
    def resolve_parameters(
        scenario_id: str,
    ) -> dict[str, Any]:
        scenario = ScenarioResolver.resolve(scenario_id)

        return {
            "scenario_name": scenario.name,
            "scenario_type": scenario.scenario_type,
            "shocks": {
                str(symbol): float(shock)
                for symbol, shock in scenario.shocks.items()
            },
            "description": scenario.descriptionm
        }