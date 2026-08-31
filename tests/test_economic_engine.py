import pytest
from decimal import Decimal
from uuid import uuid4

from src.domain import Money
from src.domain.enums import DecisionState, InterventionType
from src.decision import (
    EconomicInputs,
    calculate_expected_net_value,
    calculate_expected_recovery_value,
    calculate_expected_downside,
    estimate_intervention_cost,
)


class TestEconomicEngine:
    def test_calculate_expected_recovery_value(self):
        inputs = EconomicInputs(
            recovery_probability=Decimal("0.5"),
            recoverable_amount=Money(Decimal("1000")),
            intervention_cost=Money(Decimal("10")),
        )
        result = calculate_expected_recovery_value(inputs)
        assert result.amount == Decimal("500")

    def test_calculate_expected_recovery_zero_probability(self):
        inputs = EconomicInputs(
            recovery_probability=Decimal("0"),
            recoverable_amount=Money(Decimal("1000")),
            intervention_cost=Money(Decimal("10")),
        )
        result = calculate_expected_recovery_value(inputs)
        assert result.amount == Decimal("0")

    def test_calculate_expected_recovery_full_probability(self):
        inputs = EconomicInputs(
            recovery_probability=Decimal("1"),
            recoverable_amount=Money(Decimal("1000")),
            intervention_cost=Money(Decimal("10")),
        )
        result = calculate_expected_recovery_value(inputs)
        assert result.amount == Decimal("1000")

    def test_calculate_expected_recovery_invalid_probability_raises(self):
        inputs = EconomicInputs(
            recovery_probability=Decimal("1.5"),
            recoverable_amount=Money(Decimal("1000")),
            intervention_cost=Money(Decimal("10")),
        )
        with pytest.raises(ValueError, match="between 0 and 1"):
            calculate_expected_recovery_value(inputs)

    def test_calculate_expected_downside(self):
        inputs = EconomicInputs(
            recovery_probability=Decimal("0.5"),
            recoverable_amount=Money(Decimal("1000")),
            intervention_cost=Money(Decimal("10")),
            downside_probability=Decimal("0.1"),
            downside_cost=Money(Decimal("500")),
        )
        result = calculate_expected_downside(inputs)
        assert result.amount == Decimal("50")

    def test_calculate_expected_net_value_positive(self):
        inputs = EconomicInputs(
            recovery_probability=Decimal("0.8"),
            recoverable_amount=Money(Decimal("1000")),
            intervention_cost=Money(Decimal("50")),
            downside_probability=Decimal("0.05"),
            downside_cost=Money(Decimal("100")),
        )
        result = calculate_expected_net_value(inputs)
        assert result.expected_recovery_value.amount == Decimal("800")
        assert result.intervention_cost.amount == Decimal("50")
        assert result.expected_downside.amount == Decimal("5")
        assert result.expected_net_value.amount == Decimal("745")
        assert result.is_economically_viable is True

    def test_calculate_expected_net_value_negative(self):
        inputs = EconomicInputs(
            recovery_probability=Decimal("0.1"),
            recoverable_amount=Money(Decimal("1000")),
            intervention_cost=Money(Decimal("200")),
            downside_probability=Decimal("0.1"),
            downside_cost=Money(Decimal("500")),
        )
        result = calculate_expected_net_value(inputs)
        assert result.is_economically_viable is False

    def test_estimate_intervention_cost_retry(self):
        cost = estimate_intervention_cost(
            InterventionType.RETRY_PAYMENT,
            Money(Decimal("1000")),
        )
        assert cost.amount == Decimal("20.00")

    def test_estimate_intervention_cost_notification(self):
        cost = estimate_intervention_cost(
            InterventionType.CUSTOMER_NOTIFICATION,
            Money(Decimal("1000")),
        )
        assert cost.amount == Decimal("1.00")

    def test_estimate_intervention_cost_manual_review(self):
        cost = estimate_intervention_cost(
            InterventionType.MANUAL_REVIEW,
            Money(Decimal("1000")),
        )
        assert cost.amount == Decimal("50")

    def test_estimate_intervention_cost_with_base(self):
        cost = estimate_intervention_cost(
            InterventionType.RETRY_PAYMENT,
            Money(Decimal("1000")),
            base_cost=Money(Decimal("5")),
        )
        assert cost.amount == Decimal("5")