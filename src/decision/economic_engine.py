from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from ..domain import Money
from ..domain.enums import InterventionType


@dataclass(frozen=True)
class EconomicInputs:
    recovery_probability: Decimal
    recoverable_amount: Money
    intervention_cost: Money
    downside_probability: Decimal = Decimal("0")
    downside_cost: Money = field(default_factory=lambda: Money.zero())


@dataclass(frozen=True)
class EconomicResult:
    expected_recovery_value: Money
    intervention_cost: Money
    expected_downside: Money
    expected_net_value: Money
    is_economically_viable: bool

    def to_dict(self) -> dict:
        return {
            "expected_recovery_value": str(self.expected_recovery_value),
            "intervention_cost": str(self.intervention_cost),
            "expected_downside": str(self.expected_downside),
            "expected_net_value": str(self.expected_net_value),
            "is_economically_viable": self.is_economically_viable,
        }


def calculate_expected_recovery_value(inputs: EconomicInputs) -> Money:
    prob = inputs.recovery_probability
    if prob < 0 or prob > 1:
        raise ValueError("Recovery probability must be between 0 and 1")
    return inputs.recoverable_amount * prob


def calculate_expected_downside(inputs: EconomicInputs) -> Money:
    prob = inputs.downside_probability
    if prob < 0 or prob > 1:
        raise ValueError("Downside probability must be between 0 and 1")
    return inputs.downside_cost * prob


def calculate_expected_net_value(inputs: EconomicInputs) -> EconomicResult:
    expected_recovery = calculate_expected_recovery_value(inputs)
    expected_downside = calculate_expected_downside(inputs)
    intervention_cost = inputs.intervention_cost

    expected_net_amount = (
        expected_recovery.amount - intervention_cost.amount - expected_downside.amount
    )

    expected_net_value = Money(expected_net_amount, expected_recovery.currency)
    is_viable = expected_net_amount > 0

    return EconomicResult(
        expected_recovery_value=expected_recovery,
        intervention_cost=intervention_cost,
        expected_downside=expected_downside,
        expected_net_value=expected_net_value,
        is_economically_viable=is_viable,
    )


def estimate_intervention_cost(
    intervention_type: InterventionType,
    amount: Money,
    base_cost: Optional[Money] = None,
) -> Money:
    if base_cost is not None:
        return base_cost

    cost_multipliers = {
        InterventionType.RETRY_PAYMENT: Decimal("0.02"),
        InterventionType.CUSTOMER_NOTIFICATION: Decimal("0.001"),
        InterventionType.PAYMENT_METHOD_UPDATE: Decimal("0.005"),
        InterventionType.MANUAL_REVIEW: Decimal("50"),
        InterventionType.ESCALATION: Decimal("100"),
    }

    multiplier = cost_multipliers.get(intervention_type, Decimal("0.01"))

    if intervention_type in (InterventionType.MANUAL_REVIEW, InterventionType.ESCALATION):
        return Money(multiplier, amount.currency)

    return amount * multiplier


DEFAULT_ECONOMIC_CONFIG = {
    "min_recovery_probability": Decimal("0.1"),
    "max_intervention_cost_ratio": Decimal("0.5"),
    "default_downside_probability": Decimal("0.05"),
    "default_downside_cost_ratio": Decimal("0.1"),
}