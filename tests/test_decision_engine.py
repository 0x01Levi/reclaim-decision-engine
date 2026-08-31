import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from src.domain import Money
from src.domain.enums import DecisionState, InterventionType, FailureReason, RevenueEventStatus
from src.domain.models import Customer, Decision, FailureEvent, Merchant, RevenueEvent
from src.decision import DecisionContext, DecisionEngine, PolicyConfig


class TestDecisionEngine:
    def setup_method(self):
        self.config = PolicyConfig()
        self.engine = DecisionEngine(self.config)
        self.merchant = Merchant.create(name="Test", email="test@example.com")
        self.customer = Customer.create(merchant_id=self.merchant.id, email="customer@example.com")
        self.revenue_event = RevenueEvent.create(
            merchant_id=self.merchant.id,
            customer_id=self.customer.id,
            amount=Money(Decimal("1000")),
            description="Test payment",
        ).mark_failed()
        self.failure_event = FailureEvent.create(
            revenue_event_id=self.revenue_event.id,
            reason=FailureReason.NETWORK_ERROR,
        )

    def _create_context(self, **overrides):
        defaults = {
            "merchant": self.merchant,
            "customer": self.customer,
            "revenue_event": self.revenue_event,
            "failure_event": self.failure_event,
            "intervention_type": InterventionType.RETRY_PAYMENT,
            "recovery_probability": Decimal("0.8"),
        }
        defaults.update(overrides)
        return DecisionContext(**defaults)

    def test_decide_act_economically_viable(self):
        context = self._create_context(recovery_probability=Decimal("0.8"))
        decision = self.engine.decide(context)
        assert decision.state == DecisionState.ACT
        assert decision.confidence == Decimal("0.8")
        assert decision.policy_result is not None

    def test_decide_do_nothing_not_viable(self):
        context = self._create_context(recovery_probability=Decimal("0.1"))
        decision = self.engine.decide(context)
        assert decision.state == DecisionState.DO_NOTHING

    def test_decide_wait_moderate_probability(self):
        context = self._create_context(recovery_probability=Decimal("0.5"))
        decision = self.engine.decide(context)
        assert decision.state == DecisionState.WAIT

    def test_decide_rejected_by_policy_becomes_do_nothing(self):
        context = self._create_context(
            recovery_probability=Decimal("0.8"),
            customer=Customer(
                id=self.customer.id,
                merchant_id=self.customer.merchant_id,
                email=self.customer.email,
                phone=self.customer.phone,
                created_at=self.customer.created_at,
                total_lifetime_value=self.customer.total_lifetime_value,
                intervention_count=5,
                last_intervention_at=datetime.utcnow() - timedelta(hours=2),
            ),
        )
        decision = self.engine.decide(context)
        assert decision.state == DecisionState.DO_NOTHING
        assert decision.policy_result.name == "REJECT"

    def test_decide_escalation_approved(self):
        context = self._create_context(
            recovery_probability=Decimal("0.6"),
            intervention_type=InterventionType.ESCALATION,
        )
        decision = self.engine.decide(context)
        assert decision.state == DecisionState.ESCALATE

    def test_decide_with_ai_recommendation(self):
        context = self._create_context(
            recovery_probability=Decimal("0.8"),
            ai_recommendation=DecisionState.ACT,
            ai_confidence=Decimal("0.9"),
            ai_reasoning="AI analysis suggests high recovery",
        )
        decision = self.engine.decide(context)
        assert decision.ai_recommendation == DecisionState.ACT
        assert decision.ai_confidence == Decimal("0.9")
        assert "AI analysis" in decision.reasoning

    def test_decision_metadata(self):
        context = self._create_context(recovery_probability=Decimal("0.8"))
        decision = self.engine.decide(context)
        assert decision.revenue_event_id == self.revenue_event.id
        assert decision.customer_id == self.customer.id
        assert decision.merchant_id == self.merchant.id