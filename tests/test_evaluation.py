import pytest
from decimal import Decimal
from uuid import uuid4

from src.domain import Money
from src.domain.enums import InterventionStatus, InterventionType, RevenueEventStatus
from src.domain.models import Intervention, RecoveryOutcome, RevenueEvent
from src.evaluation import EvaluationResult, evaluate_batch, compare_baseline_vs_reclaim


class TestEvaluation:
    def setup_method(self):
        self.merchant_id = uuid4()
        self.customer_id = uuid4()

    def test_evaluate_empty_batch(self):
        result = evaluate_batch([], [], [])
        assert result.total_events == 0
        assert result.total_revenue_at_risk == Money.zero()

    def test_evaluate_no_recovery(self):
        events = [
            RevenueEvent.create(
                merchant_id=self.merchant_id,
                customer_id=self.customer_id,
                amount=Money(Decimal("1000")),
                description="Test",
            ).mark_failed()
        ]
        result = evaluate_batch(events, [], [])
        assert result.total_revenue_at_risk == Money(Decimal("1000"))
        assert result.total_recovered_revenue == Money.zero()
        assert result.recovery_rate == Decimal("0")

    def test_evaluate_with_recovery(self):
        event = RevenueEvent.create(
            merchant_id=self.merchant_id,
            customer_id=self.customer_id,
            amount=Money(Decimal("1000")),
            description="Test",
        ).mark_failed()

        outcome = RecoveryOutcome.create(
            revenue_event_id=event.id,
            recovered_amount=Money(Decimal("800")),
            intervention_id=None,
            is_natural_recovery=True,
        )

        result = evaluate_batch([event], [], [outcome])
        assert result.total_recovered_revenue == Money(Decimal("800"))
        assert result.recovered_events == 1
        assert result.natural_recovery_events == 1

    def test_evaluate_with_intervention(self):
        event = RevenueEvent.create(
            merchant_id=self.merchant_id,
            customer_id=self.customer_id,
            amount=Money(Decimal("1000")),
            description="Test",
        ).mark_failed()

        intervention = Intervention.create(
            revenue_event_id=event.id,
            customer_id=self.customer_id,
            merchant_id=self.merchant_id,
            type=InterventionStatus.COMPLETED,
            estimated_cost=Money(Decimal("20")),
        )
        intervention = intervention.mark_completed(Money(Decimal("25")))

        outcome = RecoveryOutcome.create(
            revenue_event_id=event.id,
            recovered_amount=Money(Decimal("900")),
            intervention_id=intervention.id,
            is_natural_recovery=False,
        )

        result = evaluate_batch([event], [intervention], [outcome])
        assert result.total_intervention_cost == Money(Decimal("25"))
        assert result.net_recovered_value == Money(Decimal("875"))
        assert result.intervention_recovery_events == 1

    def test_evaluate_baseline_and_incremental(self):
        event = RevenueEvent.create(
            merchant_id=self.merchant_id,
            customer_id=self.customer_id,
            amount=Money(Decimal("1000")),
            description="Test",
        ).mark_failed()

        outcome = RecoveryOutcome.create(
            revenue_event_id=event.id,
            recovered_amount=Money(Decimal("300")),
            intervention_id=None,
            is_natural_recovery=True,
        )

        result = evaluate_batch([event], [], [outcome], baseline_recovery_rate=Decimal("0.15"))
        assert result.baseline_recovery == Money(Decimal("150"))
        assert result.incremental_recovered_value == Money(Decimal("150"))

    def test_evaluate_roi(self):
        event = RevenueEvent.create(
            merchant_id=self.merchant_id,
            customer_id=self.customer_id,
            amount=Money(Decimal("1000")),
            description="Test",
        ).mark_failed()

        intervention = Intervention.create(
            revenue_event_id=event.id,
            customer_id=self.customer_id,
            merchant_id=self.merchant_id,
            type=InterventionType.RETRY_PAYMENT,
            estimated_cost=Money(Decimal("20")),
        ).mark_completed(Money(Decimal("25")))

        outcome = RecoveryOutcome.create(
            revenue_event_id=event.id,
            recovered_amount=Money(Decimal("900")),
            intervention_id=intervention.id,
            is_natural_recovery=False,
        )

        result = evaluate_batch([event], [intervention], [outcome])
        assert result.roi == Decimal("35.0")  # (900-25)/25 = 35

    def test_compare_baseline_vs_reclaim(self):
        baseline = EvaluationResult(
            total_revenue_at_risk=Money(Decimal("10000")),
            total_recovered_revenue=Money(Decimal("1500")),
            total_intervention_cost=Money(Decimal("0")),
            net_recovered_value=Money(Decimal("1500")),
            recovery_rate=Decimal("0.15"),
            intervention_rate=Decimal("0"),
            baseline_recovery=Money(Decimal("1500")),
            incremental_recovered_value=Money(Decimal("0")),
            roi=Decimal("0"),
            total_events=100,
            recovered_events=15,
            intervened_events=0,
            natural_recovery_events=15,
            intervention_recovery_events=0,
        )

        reclaim = EvaluationResult(
            total_revenue_at_risk=Money(Decimal("10000")),
            total_recovered_revenue=Money(Decimal("4000")),
            total_intervention_cost=Money(Decimal("500")),
            net_recovered_value=Money(Decimal("3500")),
            recovery_rate=Decimal("0.40"),
            intervention_rate=Decimal("0.20"),
            baseline_recovery=Money(Decimal("1500")),
            incremental_recovered_value=Money(Decimal("2500")),
            roi=Decimal("7.0"),
            total_events=100,
            recovered_events=40,
            intervened_events=20,
            natural_recovery_events=15,
            intervention_recovery_events=25,
        )

        comparison = compare_baseline_vs_reclaim(baseline, reclaim)
        assert comparison["net_improvement"] == "INR 2000.00"
        assert comparison["incremental_improvement"] == "INR 2500.00"