import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from src.domain import Money
from src.domain.enums import DecisionState, InterventionType, PolicyResult
from src.domain.models import Customer, Merchant
from src.decision import PolicyConfig, PolicyContext, PolicyEngine, EconomicResult


class TestPolicyEngine:
    def setup_method(self):
        self.config = PolicyConfig()
        self.engine = PolicyEngine(self.config)
        self.merchant = Merchant.create(name="Test", email="test@example.com")
        self.customer = Customer.create(merchant_id=self.merchant.id, email="customer@example.com")

    def _create_context(self, **overrides):
        defaults = {
            "customer_intervention_count": 0,
            "customer_last_intervention_hours_ago": None,
            "revenue_at_risk": Money(Decimal("1000")),
            "intervention_type": InterventionType.RETRY_PAYMENT,
            "intervention_cost": Money(Decimal("20")),
            "economic_result": None,
        }
        defaults.update(overrides)
        return PolicyContext(**defaults)

    def test_approve_do_nothing(self):
        context = self._create_context()
        result = self.engine.evaluate(DecisionState.DO_NOTHING, Decimal("0.5"), context)
        assert result.result == PolicyResult.APPROVE

    def test_approve_wait(self):
        context = self._create_context()
        result = self.engine.evaluate(DecisionState.WAIT, Decimal("0.5"), context)
        assert result.result == PolicyResult.APPROVE

    def test_reject_low_confidence(self):
        context = self._create_context()
        result = self.engine.evaluate(DecisionState.ACT, Decimal("0.3"), context)
        assert result.result == PolicyResult.REJECT
        assert "below threshold" in result.reason

    def test_reject_amount_exceeds_limit(self):
        context = self._create_context(revenue_at_risk=Money(Decimal("20000")))
        result = self.engine.evaluate(DecisionState.ACT, Decimal("0.8"), context)
        assert result.result == PolicyResult.ESCALATE

    def test_reject_max_interventions_exceeded(self):
        context = self._create_context(customer_intervention_count=5)
        result = self.engine.evaluate(DecisionState.ACT, Decimal("0.8"), context)
        assert result.result == PolicyResult.REJECT
        assert "exceeds limit" in result.reason

    def test_reject_cooldown_not_met(self):
        context = self._create_context(customer_last_intervention_hours_ago=12)
        result = self.engine.evaluate(DecisionState.ACT, Decimal("0.8"), context)
        assert result.result == PolicyResult.REJECT
        assert "Cooldown period not met" in result.reason

    def test_reject_cost_ratio_exceeded(self):
        context = self._create_context(intervention_cost=Money(Decimal("600")))
        result = self.engine.evaluate(DecisionState.ACT, Decimal("0.8"), context)
        assert result.result == PolicyResult.REJECT
        assert "cost ratio" in result.reason

    def test_reject_not_economically_viable(self):
        economic_result = EconomicResult(
            expected_recovery_value=Money(Decimal("100")),
            intervention_cost=Money(Decimal("200")),
            expected_downside=Money(Decimal("10")),
            expected_net_value=Money(Decimal("-110")),
            is_economically_viable=False,
        )
        context = self._create_context(economic_result=economic_result)
        result = self.engine.evaluate(DecisionState.ACT, Decimal("0.8"), context)
        assert result.result == PolicyResult.REJECT
        assert "economically viable" in result.reason

    def test_approve_act_all_checks_pass(self):
        economic_result = EconomicResult(
            expected_recovery_value=Money(Decimal("800")),
            intervention_cost=Money(Decimal("50")),
            expected_downside=Money(Decimal("5")),
            expected_net_value=Money(Decimal("745")),
            is_economically_viable=True,
        )
        context = self._create_context(economic_result=economic_result)
        result = self.engine.evaluate(DecisionState.ACT, Decimal("0.8"), context)
        assert result.result == PolicyResult.APPROVE

    def test_approve_escalation(self):
        context = self._create_context()
        result = self.engine.evaluate(DecisionState.ESCALATE, Decimal("0.8"), context)
        assert result.result == PolicyResult.APPROVE