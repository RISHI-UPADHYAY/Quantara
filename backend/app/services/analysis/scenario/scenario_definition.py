from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping



@dataclass(frozen=True)
class ScenarioDefinition:
    """
    Immutable definition of a deterministic portfolio stress scenario.

    A scenario contains metadata and asset-level price shocks.
    """

    name: str
    scenario_type: str
    shocks: Mapping[str, float]
    description: str = ""


    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.scenario_type,
            "shocks": dict(self.shocks),
            "description": self.description,
        }