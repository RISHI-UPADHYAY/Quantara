from __future__ import annotations

from decimal import Decimal


class ExecutionDiagnosisEngine:
    """
    Deterministic execution-diagnoses engine.

    Quantara v1 diagnoses execution quality using TCA metrics.

    The diagnoses engine is intentionally separate from the 
    Execution Quality Score model.

    Positive/adverse values indicate worse execution.

    v1 does not make casual claims. In particular, market impact represents
    adverse market movement during the execution window,
    not proven price movement caused by the trader's order.
    """

    # diagnoses thresholds are percentages.
    # These are initial Quantara v1 heuristics and are not intended to represent universal institutional benchmarks.

    SLIPPAGE_THRESHOLD = Decimal("0.10")
    MARKET_VWAP_THRESHOLD = Decimal("0.10")
    SHORTFALL_THRESHOLD = Decimal("0.15")
    MARKET_IMPACT_THRESHOLD = Decimal("0.10")
    EXPLICIT_COST_THRESHOLD = Decimal("0.05")

    def calculate_execution_diagnoses(
        self,
        *,
        arrival_price: float | Decimal,
        execution_price: float | Decimal,
        market_vwap: float | Decimal,
        end_market_price: float | Decimal,
        total_slippage: float | Decimal,
        total_shortfall: float | Decimal,
        total_market_impact: float | Decimal,
        commission: float | Decimal,
        fees: float | Decimal,
        executed_quantity: float | Decimal,
        side: str,
    ) -> dict:

        arrival = Decimal(str(arrival_price))
        execution = Decimal(str(execution_price))
        vwap = Decimal(str(market_vwap))
        end_price = Decimal(str(end_market_price))
        slippage = Decimal(str(total_slippage))
        shortfall = Decimal(str(total_shortfall))
        market_impact = Decimal(str(total_market_impact))
        commission_value = Decimal(str(commission))
        fees_value = Decimal(str(fees))
        quantity = Decimal(str(executed_quantity))

        self._validate_inputs(
            arrival=arrival,
            execution=execution,
            vwap=vwap,
            end_price=end_price,
            quantity=quantity,
            side=side,
        )

        diagnoses: list[dict] = []

        # 1. Slippage
        slippage_percentage = (
            slippage / (arrival * quantity)
        ) * Decimal("100")

        self._append_diagnosis(
            diagnoses=diagnoses,
            code="HIGH_SLIPPAGE",
            severity=self._severity_for_percentage(
                slippage_percentage,
                self.SLIPPAGE_THRESHOLD,
            ),
            triggered=slippage_percentage > self.SLIPPAGE_THRESHOLD,
            message=(
                "Execution experienced elevated slippage relative to the arrival price."
            ),
            evidence= {
                "slippage_percentage": float(slippage_percentage),
                "threshold": float(self.SLIPPAGE_THRESHOLD),
                "arrival_price": float(arrival),
                "execution_price": float(execution),
            },
        )

        # 2. Market VWAP performance
        if side == "buy":
            vwap_deviation = execution - vwap

        else:
            vwap_deviation = vwap - execution

        vwap_percentage = (
            vwap_deviation / vwap
        ) * Decimal("100")

        self._append_diagnosis(
            diagnoses=diagnoses,
            code="POOR_VWAP_PERFORMANCE",
            severity=self._severity_for_percentage(
                vwap_percentage,
                self.MARKET_VWAP_THRESHOLD,
            ),
            triggered=vwap_percentage > self.MARKET_VWAP_THRESHOLD,
            message=(
                "Execution performed materially worse than the market VWAP during the execution window."
            ),
            evidence= {
                "execution_price": float(execution),
                "market_vwap": float(vwap),
                "vwap_deviation_percentage": float(vwap_percentage),
                "threshold": float(self.MARKET_VWAP_THRESHOLD),
            },
        )

        # 3. Implementation Shortfall
        shortfall_percentage = (
            shortfall / (arrival * quantity)
        ) * Decimal("100")

        self._append_diagnosis(
            diagnoses=diagnoses,
            code="HIGH_IMPLEMENTATION_SHORTFALL",
            severity=self._severity_for_percentage(
                shortfall_percentage,
                self.SHORTFALL_THRESHOLD,
            ),
            triggered=shortfall_percentage > self.SHORTFALL_THRESHOLD,
            message=(
                "Execution incurred elevated implementation "
                "shortfall relative to the arrival price."
            ),
            evidence= {
                "shortfall_percentage": float(shortfall_percentage),
                "threshold": float(self.SHORTFALL_THRESHOLD),
                "total_shortfall": float(shortfall),
            },
        )

        # 4. Market Impact
        market_impact_percentage = (
            market_impact / (arrival * quantity)
        ) * Decimal("100")

        self._append_diagnosis(
            diagnoses=diagnoses,
            code="HIGH_MARKET_IMPACT",
            severity=self._severity_for_percentage(
                market_impact_percentage,
                self.MARKET_IMPACT_THRESHOLD,
            ),
            triggered=market_impact_percentage > self.MARKET_IMPACT_THRESHOLD,
            message=(
                "The market moved adversely during the execution window."
            ),
            evidence= {
                "market_impact_percentage": float(market_impact_percentage),
                "threshold": float(self.MARKET_IMPACT_THRESHOLD),
                "arrival_price": float(arrival),
                "execution_market_price": float(end_price),
                "total_market_impact": float(market_impact),
            },
        )

        # 5. Explicit transaction costs
        explicit_costs = commission_value + fees_value

        explicit_cost_percentage = (
            explicit_costs / (arrival * quantity)
        ) * Decimal("100")

        self._append_diagnosis(
            diagnoses=diagnoses,
            code="HIGH_TRANSACTION_COSTS",
            severity=self._severity_for_percentage(
                explicit_cost_percentage,
                self.EXPLICIT_COST_THRESHOLD,
            ),
            triggered=explicit_cost_percentage > self.EXPLICIT_COST_THRESHOLD,
            message=(
                "Commission and fees represent a material "
                "portion of execution cost."
            ),
            evidence= {
                "commission": float(commission_value),
                "fees": float(fees_value),
                "explicit_costs": float(explicit_costs),
                "explicit_cost_percentage": float(explicit_cost_percentage),
                "threshold": float(self.EXPLICIT_COST_THRESHOLD),
            },
        )

        # 6. Overall Status
        overall_status = self._overall_status(diagnoses)

        #If not adverse diagnoses was triggered, explicitly record 
        #that the execution did not show a material issue.
        if not diagnoses:
            diagnoses.append(
                {
                    "code": "GOOD_EXECUTION",
                    "severity": "INFO",
                    "message": (
                        "No material execution-cost issue was "
                        "identified by the configured v1 diagnosis rules."
                    ),
                    "evidence": {
                        "slippage_percentage": float(slippage_percentage),
                        "vwap_deviation_percentage": float(vwap_percentage),
                        "shortfall_percentage": float(shortfall_percentage),
                        "market_impact_percentage": float(market_impact_percentage),
                        "explicit_cost_percentage": float(explicit_cost_percentage),
                    },
                }
            )

        return {
            "overall_status": overall_status,
            "diagnoses": diagnoses,
        }


    @staticmethod
    def _append_diagnosis(
        *,
        diagnoses: list[dict],
        code: str,
        severity: str,
        triggered: bool,
        message: str,
        evidence: dict,
    ) -> None:
        if not triggered:
            return

        diagnoses.append(
            {
                "code": code,
                "severity": severity,
                "message": message,
                "evidence": evidence,
            }
        )


    @staticmethod
    def _severity_for_percentage(
        percentage: Decimal,
        threshold: Decimal,
    ) -> str:
        if percentage <= threshold:
            return "INFO"

        ratio = percentage / threshold

        if ratio >= Decimal("3"):
            return "CRITICAL"

        if ratio >= Decimal("2"):
            return "HIGH"

        return "MEDIUM"



    @staticmethod
    def _overall_status(
        diagnoses: list[dict],
    ) -> str:
        if any(
            diagnosis["severity"] == "CRITICAL"
            for diagnosis in diagnoses
        ):
            return "CRITICAL"

        if any(
            diagnosis["severity"] == "HIGH"
            for diagnosis in diagnoses
        ):
            return "NEEDS_ATTENTION"

        if any(
            diagnosis["severity"] == "MEDIUM"
            for diagnosis in diagnoses
        ):
            return "NEEDS_ATTENTION"

        return "HEALTHY"


    @staticmethod
    def _validate_inputs(
        *,
        arrival: Decimal,
        execution: Decimal,
        vwap: Decimal,
        end_price: Decimal,
        quantity: Decimal,
        side: str,
    ) -> None:
        if side not in {"buy", "sell"}:
            raise ValueError(
                f"Unsupported execution side: {side}."
            )

        if arrival <= Decimal("0"):
            raise ValueError(
                "Arrival price must be greater than zero."
            )

        if execution <= Decimal("0"):
            raise ValueError(
                "Execution price must be greater than zero."
            )

        if vwap <= Decimal("0"):
            raise ValueError(
                "Market VWAP must be greater than zero."
            )

        if quantity <= Decimal("0"):
            raise ValueError(
                "Executed quantity must be greater than zero."
            )

        if end_price <= Decimal("0"):
            raise ValueError(
                "End market price must be greater than zero."
            ) 