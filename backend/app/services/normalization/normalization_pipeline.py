from pathlib import Path
from typing import Any

import pandas as pd

from app.services.normalization.market_data_normalizer import MarketDataNormalizer
from app.services.normalization.normalization_validator import NormalizationValidator

class NormalizationPipeline:

    def __init__(self):
        self.normalizer = MarketDataNormalizer()
        self.validator = NormalizationValidator()

    def process(
        self,
        file_path: Path,
    ) -> dict[str, Any]:

        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        dataframe, normalization_report = (
            self.normalizer.normalize(
                file_path
            )
        )

        validation_report = self.validator.validate(
            dataframe
        )

        status = (
            "valid"
            if validation_report["valid"]
            else "invalid"
        )

        return {
            "data": dataframe,
            "normalization": normalization_report,
            "validation": validation_report,
            "status": status,
        }