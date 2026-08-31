import pytest
from decimal import Decimal
from uuid import uuid4

from src.domain import Money
from src.domain.enums import FailureReason, InterventionType
from src.simulator import Scenario, SyntheticDataGenerator, create_deterministic_batch


class TestSyntheticDataGenerator:
    def test_deterministic_generation(self):
        batch1 = create_deterministic_batch(seed=42, count=10)
        batch2 = create_deterministic_batch(seed=42, count=10)
        batch3 = create_deterministic_batch(seed=123, count=10)

        assert len(batch1) == 10
        assert len(batch2) == 10
        assert len(batch3) == 10

        for s1, s2 in zip(batch1, batch2):
            assert s1.name == s2.name
            assert s1.recovery_probability == s2.recovery_probability
            assert s1.intervention_type == s2.intervention_type

        assert batch1[0].name != batch3[0].name or batch1[0].recovery_probability != batch3[0].recovery_probability

    def test_scenario_types_present(self):
        batch = create_deterministic_batch(seed=42, count=100)
        scenario_names = {s.name for s in batch}

        expected_types = {
            "transient_failure",
            "insufficient_funds",
            "repeated_failure",
            "customer_action_required",
            "natural_recovery",
            "unrecoverable",
            "intervention_fatigue",
            "escalation_case",
        }

        for expected in expected_types:
            assert expected in scenario_names, f"Missing scenario type: {expected}"

    def test_scenario_structure(self):
        batch = create_deterministic_batch(seed=42, count=1)
        scenario = batch[0]

        assert isinstance(scenario, Scenario)
        assert scenario.merchant is not None
        assert scenario.customer is not None
        assert scenario.revenue_event is not None
        assert scenario.failure_event is not None
        assert isinstance(scenario.recovery_probability, Decimal)
        assert scenario.intervention_type in InterventionType
        assert isinstance(scenario.expected_natural_recovery, bool)

    def test_revenue_event_failed_status(self):
        batch = create_deterministic_batch(seed=42, count=10)
        for scenario in batch:
            assert scenario.revenue_event.status.name == "FAILED"

    def test_failure_event_linked(self):
        batch = create_deterministic_batch(seed=42, count=10)
        for scenario in batch:
            assert scenario.failure_event.revenue_event_id == scenario.revenue_event.id

    def test_customer_linked_to_merchant(self):
        batch = create_deterministic_batch(seed=42, count=10)
        for scenario in batch:
            assert scenario.customer.merchant_id == scenario.merchant.id
            assert scenario.revenue_event.merchant_id == scenario.merchant.id
            assert scenario.revenue_event.customer_id == scenario.customer.id

    def test_intervention_fatigue_scenario(self):
        generator = SyntheticDataGenerator(seed=42)
        merchant = generator.generate_merchant()
        scenarios = generator.generate_scenario_batch(merchant, 100)

        fatigue_scenarios = [s for s in scenarios if s.name == "intervention_fatigue"]
        assert len(fatigue_scenarios) > 0

        for scenario in fatigue_scenarios:
            assert scenario.customer.intervention_count >= 3
            assert scenario.customer.last_intervention_at is not None

    def test_repeated_failure_scenario(self):
        generator = SyntheticDataGenerator(seed=42)
        merchant = generator.generate_merchant()
        scenarios = generator.generate_scenario_batch(merchant, 100)

        repeated = [s for s in scenarios if s.name == "repeated_failure"]
        assert len(repeated) > 0

        for scenario in repeated:
            assert scenario.failure_event.retry_count >= 3

    def test_escalation_case_high_amount(self):
        generator = SyntheticDataGenerator(seed=42)
        merchant = generator.generate_merchant()
        scenarios = generator.generate_scenario_batch(merchant, 100)

        escalations = [s for s in scenarios if s.name == "escalation_case"]
        assert len(escalations) > 0

        for scenario in escalations:
            assert scenario.revenue_event.amount.amount >= Decimal("50000")

    def test_unrecoverable_low_probability(self):
        generator = SyntheticDataGenerator(seed=42)
        merchant = generator.generate_merchant()
        scenarios = generator.generate_scenario_batch(merchant, 100)

        unrecoverable = [s for s in scenarios if s.name == "unrecoverable"]
        assert len(unrecoverable) > 0

        for scenario in unrecoverable:
            assert scenario.recovery_probability < Decimal("0.1")
            assert scenario.failure_event.reason == FailureReason.FRAUD_SUSPECTED