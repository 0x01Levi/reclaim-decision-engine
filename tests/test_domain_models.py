import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

from src.domain import Money
from src.domain.enums import (
    DecisionState,
    FailureReason,
    InterventionStatus,
    InterventionType,
    PolicyResult,
    RevenueEventStatus,
)
from src.domain.models import (
    AuditEvent,
    Customer,
    Decision,
    FailureEvent,
    Intervention,
    Merchant,
    RecoveryOutcome,
    RevenueEvent,
)


class TestDomainModels:
    def test_merchant_create(self):
        merchant = Merchant.create(name="Test Merchant", email="test@example.com")
        assert merchant.name == "Test Merchant"
        assert merchant.email == "test@example.com"
        assert merchant.risk_tier == "STANDARD"

    def test_customer_create(self):
        merchant_id = uuid4()
        customer = Customer.create(merchant_id=merchant_id, email="customer@example.com")
        assert customer.merchant_id == merchant_id
        assert customer.intervention_count == 0
        assert customer.last_intervention_at is None

    def test_revenue_event_create(self):
        merchant_id = uuid4()
        customer_id = uuid4()
        event = RevenueEvent.create(
            merchant_id=merchant_id,
            customer_id=customer_id,
            amount=Money(Decimal("1000")),
            description="Test payment",
        )
        assert event.status == RevenueEventStatus.PENDING
        assert event.amount == Money(Decimal("1000"))

    def test_revenue_event_mark_failed(self):
        event = RevenueEvent.create(
            merchant_id=uuid4(),
            customer_id=uuid4(),
            amount=Money(Decimal("1000")),
            description="Test",
        )
        failed = event.mark_failed()
        assert failed.status == RevenueEventStatus.FAILED
        assert failed.id == event.id

    def test_revenue_event_mark_recovered(self):
        event = RevenueEvent.create(
            merchant_id=uuid4(),
            customer_id=uuid4(),
            amount=Money(Decimal("1000")),
            description="Test",
        )
        recovered = event.mark_recovered()
        assert recovered.status == RevenueEventStatus.RECOVERED

    def test_revenue_event_mark_unrecoverable(self):
        event = RevenueEvent.create(
            merchant_id=uuid4(),
            customer_id=uuid4(),
            amount=Money(Decimal("1000")),
            description="Test",
        )
        unrecoverable = event.mark_unrecoverable()
        assert unrecoverable.status == RevenueEventStatus.UNRECOVERABLE

    def test_failure_event_create(self):
        revenue_event_id = uuid4()
        failure = FailureEvent.create(
            revenue_event_id=revenue_event_id,
            reason=FailureReason.INSUFFICIENT_FUNDS,
            error_code="INSUFFICIENT_FUNDS",
        )
        assert failure.reason == FailureReason.INSUFFICIENT_FUNDS
        assert failure.retry_count == 0

    def test_failure_event_with_retry(self):
        failure = FailureEvent.create(
            revenue_event_id=uuid4(),
            reason=FailureReason.NETWORK_ERROR,
        )
        retried = failure.with_retry()
        assert retried.retry_count == 1
        assert retried.id == failure.id

    def test_intervention_create(self):
        intervention = Intervention.create(
            revenue_event_id=uuid4(),
            customer_id=uuid4(),
            merchant_id=uuid4(),
            type=InterventionType.RETRY_PAYMENT,
            estimated_cost=Money(Decimal("10")),
        )
        assert intervention.status == InterventionStatus.PENDING
        assert intervention.idempotency_key is not None

    def test_intervention_state_transitions(self):
        intervention = Intervention.create(
            revenue_event_id=uuid4(),
            customer_id=uuid4(),
            merchant_id=uuid4(),
            type=InterventionType.RETRY_PAYMENT,
            estimated_cost=Money(Decimal("10")),
        )

        executing = intervention.mark_executing()
        assert executing.status == InterventionStatus.EXECUTING
        assert executing.executed_at is not None

        completed = executing.mark_completed(Money(Decimal("12")))
        assert completed.status == InterventionStatus.COMPLETED
        assert completed.actual_cost == Money(Decimal("12"))
        assert completed.completed_at is not None

        failed = intervention.mark_failed()
        assert failed.status == InterventionStatus.FAILED

        skipped = intervention.mark_skipped()
        assert skipped.status == InterventionStatus.SKIPPED

    def test_recovery_outcome_create(self):
        outcome = RecoveryOutcome.create(
            revenue_event_id=uuid4(),
            recovered_amount=Money(Decimal("500")),
            intervention_id=uuid4(),
            is_natural_recovery=False,
        )
        assert outcome.recovered_amount == Money(Decimal("500"))
        assert outcome.is_natural_recovery is False

    def test_decision_create(self):
        decision = Decision.create(
            revenue_event_id=uuid4(),
            customer_id=uuid4(),
            merchant_id=uuid4(),
            state=DecisionState.ACT,
            confidence=Decimal("0.8"),
            reasoning="High recovery probability",
        )
        assert decision.state == DecisionState.ACT
        assert decision.confidence == Decimal("0.8")

    def test_decision_with_policy_result(self):
        decision = Decision.create(
            revenue_event_id=uuid4(),
            customer_id=uuid4(),
            merchant_id=uuid4(),
            state=DecisionState.ACT,
            confidence=Decimal("0.8"),
            reasoning="Test",
        )
        with_policy = decision.with_policy_result(PolicyResult.APPROVE, "All checks passed")
        assert with_policy.policy_result == PolicyResult.APPROVE
        assert with_policy.policy_reason == "All checks passed"

    def test_audit_event_create(self):
        audit = AuditEvent.create(
            event_type="decision_made",
            entity_type="decision",
            entity_id=uuid4(),
            merchant_id=uuid4(),
            payload={"state": "ACT", "confidence": "0.8"},
        )
        assert audit.event_type == "decision_made"
        assert audit.payload["state"] == "ACT"