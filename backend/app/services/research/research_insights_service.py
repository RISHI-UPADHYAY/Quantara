from __future__ import annotations

from typing import Any


class ResearchInsightsService:
    """
    Generate deterministic, structured research insights from Quantara's
    quantitative research context.

    This service does not use an LLM and does not invent metrics.
    """

    def generate(
        self,
        *,
        context_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not isinstance(context_result, dict):
            raise ValueError("context_result must be a dictionary.")

        context = context_result.get("context", {})
        if not isinstance(context, dict):
            raise ValueError("context_result.context must be a dictionary.")

        analyses = context.get("analyses", {})
        if not isinstance(analyses, dict):
            analyses = {}

        insights: list[dict[str, Any]] = []

        self._add_performance_insights(
            insights=insights,
            analyses=analyses,
        )

        self._add_risk_insights(
            insights=insights,
            analyses=analyses,
        )

        self._add_relationship_insights(
            insights=insights,
            analyses=analyses,
        )

        self._add_benchmark_insights(
            insights=insights,
            context=context,
        )

        self._add_data_quality_insights(
            insights=insights,
            context=context,
        )

        if not insights:
            insights.append(
                {
                    "category": "summary",
                    "title": "No quantitative insight available",
                    "description": (
                        "The available research context does not contain "
                        "sufficient quantitative evidence to generate a "
                        "specific research insight."
                    ),
                    "severity": "info",
                    "evidence": [],
                }
            )

        return insights

    @staticmethod
    def _add_performance_insights(
        *,
        insights: list[dict[str, Any]],
        analyses: dict[str, Any],
    ) -> None:
        returns = analyses.get("returns")

        if not isinstance(returns, dict):
            return

        cumulative_return = returns.get("cumulative_return")

        if not isinstance(cumulative_return, (int, float)):
            return

        percentage = cumulative_return * 100

        if cumulative_return > 0:
            direction = "positive"
            severity = "positive"
            description = (
                f"The analyzed dataset produced a cumulative return of "
                f"{percentage:.4f}% over the available observation period."
            )
        elif cumulative_return < 0:
            direction = "negative"
            severity = "warning"
            description = (
                f"The analyzed dataset produced a cumulative return of "
                f"{percentage:.4f}% over the available observation period."
            )
        else:
            direction = "flat"
            severity = "info"
            description = (
                "The analyzed dataset produced a cumulative return of "
                "0.0000% over the available observation period."
            )

        insights.append(
            {
                "category": "performance",
                "title": f"{direction.capitalize()} cumulative return",
                "description": description,
                "severity": severity,
                "evidence": [
                    {
                        "source": "returns",
                        "metric": "cumulative_return",
                        "value": cumulative_return,
                        "interpretation": (
                            "Cumulative return over the analyzed observation period."
                        ),
                    }
                ],
            }
        )

    @staticmethod
    def _add_risk_insights(
        *,
        insights: list[dict[str, Any]],
        analyses: dict[str, Any],
    ) -> None:
        volatility = analyses.get("volatility")
        drawdown = analyses.get("drawdown")

        if isinstance(volatility, dict):
            volatility_data = volatility.get("volatility", {})
            if isinstance(volatility_data, dict):
                annualized = volatility_data.get("annualized")

                if isinstance(annualized, (int, float)):
                    insights.append(
                        {
                            "category": "risk",
                            "title": "Observed annualized volatility",
                            "description": (
                                f"The annualized volatility calculated from "
                                f"the available return observations is "
                                f"{annualized * 100:.4f}%."
                            ),
                            "severity": "info",
                            "evidence": [
                                {
                                    "source": "volatility",
                                    "metric": "annualized_volatility",
                                    "value": annualized,
                                    "interpretation": (
                                        "Annualized volatility based on the "
                                        "configured periods-per-year assumption."
                                    ),
                                }
                            ],
                        }
                    )

        if isinstance(drawdown, dict):
            drawdown_data = drawdown.get("drawdown", {})

            if isinstance(drawdown_data, dict):
                maximum = drawdown_data.get("maximum")

                if isinstance(maximum, (int, float)):
                    if maximum < 0:
                        severity = "warning"
                        title = "Observed maximum drawdown"
                        description = (
                            f"The maximum observed drawdown was "
                            f"{maximum * 100:.4f}%."
                        )
                    else:
                        severity = "info"
                        title = "No observed drawdown"
                        description = (
                            "No drawdown was observed in the available "
                            "price sequence."
                        )

                    insights.append(
                        {
                            "category": "risk",
                            "title": title,
                            "description": description,
                            "severity": severity,
                            "evidence": [
                                {
                                    "source": "drawdown",
                                    "metric": "maximum_drawdown",
                                    "value": maximum,
                                    "interpretation": (
                                        "Maximum drawdown observed in the "
                                        "available price sequence."
                                    ),
                                }
                            ],
                        }
                    )

    @staticmethod
    def _add_relationship_insights(
        *,
        insights: list[dict[str, Any]],
        analyses: dict[str, Any],
    ) -> None:
        correlation = analyses.get("correlation")

        if not isinstance(correlation, dict):
            return

        strongest_positive = correlation.get("strongest_positive")
        strongest_negative = correlation.get("strongest_negative")

        if isinstance(strongest_positive, dict):
            value = strongest_positive.get("correlation")

            if isinstance(value, (int, float)):
                insights.append(
                    {
                        "category": "relationship",
                        "title": "Strongest positive correlation",
                        "description": (
                            "The strongest positive relationship identified "
                            f"has a correlation of {value:.4f}."
                        ),
                        "severity": "info",
                        "evidence": [
                            {
                                "source": "correlation",
                                "metric": "strongest_positive_correlation",
                                "value": strongest_positive,
                                "interpretation": (
                                    "Strongest positive cross-symbol return relationship."
                                ),
                            }
                        ],
                    }
                )

        if isinstance(strongest_negative, dict):
            value = strongest_negative.get("correlation")

            if isinstance(value, (int, float)):
                insights.append(
                    {
                        "category": "relationship",
                        "title": "Strongest negative correlation",
                        "description": (
                            "The strongest negative relationship identified "
                            f"has a correlation of {value:.4f}."
                        ),
                        "severity": "info",
                        "evidence": [
                            {
                                "source": "correlation",
                                "metric": "strongest_negative_correlation",
                                "value": strongest_negative,
                                "interpretation": (
                                    "Strongest negative cross-symbol return relationship."
                                ),
                            }
                        ],
                    }
                )

    @staticmethod
    def _add_benchmark_insights(
        *,
        insights: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> None:
        beta_comparisons = context.get("beta_comparisons")

        if not isinstance(beta_comparisons, list):
            return

        for comparison in beta_comparisons:
            if not isinstance(comparison, dict):
                continue

            beta = comparison.get("beta")

            if not isinstance(beta, (int, float)):
                continue

            symbol = comparison.get("symbol", "Asset")
            benchmark = comparison.get("benchmark", "benchmark")

            insights.append(
                {
                    "category": "benchmark",
                    "title": f"{symbol} beta versus {benchmark}",
                    "description": (
                        f"The calculated beta for {symbol} relative to "
                        f"{benchmark} is {beta:.4f}."
                    ),
                    "severity": "info",
                    "evidence": [
                        {
                            "source": "beta",
                            "metric": "beta",
                            "value": beta,
                            "interpretation": (
                                "Estimated sensitivity of the asset's returns "
                                "relative to the selected benchmark."
                            ),
                        }
                    ],
                }
            )

    @staticmethod
    def _add_data_quality_insights(
        *,
        insights: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> None:
        data_quality = context.get("data_quality")

        if not isinstance(data_quality, dict):
            return

        quality = data_quality.get("quality")

        if not isinstance(quality, dict):
            return

        score = quality.get("quality_score")
        status = quality.get("status")
        research_ready = quality.get("research_ready")

        if isinstance(score, (int, float)):
            if score >= 90:
                severity = "positive"
                title = "Excellent data quality"
                description = (
                    f"The dataset received a data quality score of {score:.0f} "
                    "and is suitable for the supported research workflows."
                )
            elif score >= 70:
                severity = "info"
                title = "Good data quality"
                description = (
                    f"The dataset received a data quality score of {score:.0f}. "
                    "Some limitations may require review before more advanced analysis."
                )
            else:
                severity = "warning"
                title = "Data quality requires review"
                description = (
                    f"The dataset received a data quality score of {score:.0f}. "
                    "The identified quality limitations should be reviewed."
                )

            evidence = [
                {
                    "source": "data_quality",
                    "metric": "quality_score",
                    "value": score,
                    "interpretation": (
                        f"Quantara data quality status: {status}."
                    ),
                }
            ]

            if research_ready is not None:
                evidence.append(
                    {
                        "source": "data_quality",
                        "metric": "research_ready",
                        "value": research_ready,
                        "interpretation": (
                            "Whether Quantara considers the dataset ready "
                            "for the supported research workflows."
                        ),
                    }
                )

            insights.append(
                {
                    "category": "data_quality",
                    "title": title,
                    "description": description,
                    "severity": severity,
                    "evidence": evidence,
                }
            )