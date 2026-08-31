import pytest
from decimal import Decimal
from uuid import uuid4

from src.domain import Money
from src.domain.enums import InterventionStatus, InterventionType, RevenueEventStatus
from src.domain.models import Customer, Intervention, Merchant, RecoveryOutcome, RevenueEvent
from src.simulator import Simulator, SimulatorState


class TestSimulator:
    def setup_method(self):
        self.merchant = Merchant.create(name="Test", email="test@example.com")
        self.customer = Customer.create(merchant_id=self.merchant.id, email="customer@example.com")
        self.revenue_event = RevenueEvent.create(
            merchant_id=self.merchant.id,
            customer_id=self.customer.id,
            amount=Money(Decimal("1000")),
            description="Test",
        ).mark_failed()

    def test_initial_state(self):
        simulator = Simulator()
        assert simulator.state.merchant is not None
        assert len(simulator.state.customers) == 0
        assert len(simulator.state.revenue_events) == 0

    def test_add_revenue_event(self):
        simulator = Simulator().add_revenue_event(self.revenue_event)
        assert len(simulator.state.revenue_events) == 1
        assert simulator.state.revenue_events[0].id == self.revenue_event.id

    def test_add_customer(self):
        simulator = Simulator().add_customer(self.customer)
        assert len(simulator.state.customers) == 1

    def test_execute_intervention_success(self):
        intervention = Intervention.create(
            revenue_event_id=self.revenue_event.id,
            customer_id=self.customer.id,
            merchant_id=self.merchant.id,
            type=InterventionType.RETRY_PAYMENT,
            estimated_cost=Money(Decimal("20")),
        )

        simulator = (
            Simulator()
            .add_revenue_event(self.revenue_event)
            .add_customer(self.customer)
            .execute_intervention(intervention, success=True, actual_cost=Money(Decimal("25")))
        )

        completed = [i for i in simulator.state.interventions if i.status == InterventionStatus.COMPLETED]
        assert len(completed) == 1
        assert completed[0].actual_cost == Money(Decimal("25"))

    def test_execute_intervention_failure(self):
        intervention = Intervention.create(
            revenue_event_id=self.revenue_event.id,
            customer_id=self.customer.id,
            merchant_id=self.merchant.id,
            type=InterventionType.RETRY_PAYMENT,
            estimated_cost=Money(Decimal("20")),
        )

        simulator = (
            Simulator()
            .add_revenue_event(self.revenue_event)
            .add_customer(self.customer)
            .execute_intervention(intervention, success=False, actual_cost=Money(Decimal("25")))
        )

        failed = [i for i in simulator.state.interventions if i.status == InterventionStatus.FAILED]
        assert len(failed) == 1

    def test_record_recovery(self):
        simulator = (
            Simulator()
            .add_revenue_event(self.revenue_event)
            .record_recovery(self.revenue_event.id, Money(Decimal("800")))
        )

        outcomes = simulator.state.recovery_outcomes
        assert len(outcomes) == 1
        assert outcomes[0].recovered_amount == Money(Decimal("800"))
        assert outcomes[0].is_natural_recovery is True

    def test_record_recovery_with_intervention(self):
        intervention_id = uuid4()
        simulator = (
            Simulator()
            .add_revenue_event(self.revenue_event)
            .record_recovery(self.revenue_event.id, Money(Decimal("900")), intervention_id=intervention_id)
        )

        outcomes = simulator.state.recovery_outcomes
        assert outcomes[0].intervention_id == intervention_id
        assert outcomes[0].is_natural_recovery is False

    def test_get_failed_events(self):
        event1 = RevenueEvent.create(
            merchant_id=self.merchant.id,
            customer_id=self.customer.id,
            amount=Money(Decimal("1000")),
            description="Test 1",
        ).mark_failed()

        event2 = RevenueEvent.create(
            merchant_id=self.merchant.id,
            customer_id=self.customer.id,
            amount=Money(Decimal("2000")),
            description="Test 2",
        ).mark_failed()

        event3 = RevenueEvent.create(
            merchant_id=self.merchant.id,
            customer_id=self.customer.id,
            amount=Money(Decimal("3000")),
            description="Test 3",
        ).mark_recovered()

        simulator = Simulator()
        simulator = simulator.add_revenue_event(event1)
        simulator = simulator.add_revenue_event(event2)
        simulator = simulator.add_revenue_event(event3)

        failed = simulator.get_failed_events()
        assert len(failed) == 2

    def test_get_pending_interventions(self):
        intervention1 = Intervention.create(
            revenue_event_id=uuid4(),
            customer_id=self.customer.id,
            merchant_id=self.merchant.id,
            type=InterventionType.RETRY_PAYMENT,
            estimated_cost=Money(Decimal("10")),
        )

        intervention2 = intervention1.mark_completed(Money(Decimal("15")))

        simulator = Simulator()
        simulator.state = SimulatorState(
            merchant=self.merchant,
            customers=[self.customer],
            revenue_events=[],
            interventions=[intervention1, intervention2],
            recovery_outcomes=[],
        )

        pending = simulator.get_pending_interventions()
        assert len(pending) == 1
        assert pending[0].status == InterventionStatus.PENDING