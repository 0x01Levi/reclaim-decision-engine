from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from ..domain import Money
from ..domain.enums import InterventionStatus, RevenueEventStatus
from ..domain.models import Customer, Intervention, Merchant, RecoveryOutcome, RevenueEvent


@dataclass(frozen=True)
class SimulatorState:
    merchant: Merchant
    customers: List[Customer]
    revenue_events: List[RevenueEvent]
    interventions: List[Intervention]
    recovery_outcomes: List[RecoveryOutcome]
    current_time: datetime = field(default_factory=datetime.utcnow)


class Simulator:
    def __init__(self, initial_state: Optional[SimulatorState] = None):
        self.state = initial_state or SimulatorState(
            merchant=Merchant.create(name="Default", email="default@example.com"),
            customers=[],
            revenue_events=[],
            interventions=[],
            recovery_outcomes=[],
        )

    def add_revenue_event(self, revenue_event: RevenueEvent) -> "Simulator":
        events = self.state.revenue_events + [revenue_event]
        return Simulator(SimulatorState(
            merchant=self.state.merchant,
            customers=self.state.customers,
            revenue_events=events,
            interventions=self.state.interventions,
            recovery_outcomes=self.state.recovery_outcomes,
            current_time=self.state.current_time,
        ))

    def add_customer(self, customer: Customer) -> "Simulator":
        customers = self.state.customers + [customer]
        return Simulator(SimulatorState(
            merchant=self.state.merchant,
            customers=customers,
            revenue_events=self.state.revenue_events,
            interventions=self.state.interventions,
            recovery_outcomes=self.state.recovery_outcomes,
            current_time=self.state.current_time,
        ))

    def execute_intervention(
        self,
        intervention: Intervention,
        success: bool,
        actual_cost: Money,
    ) -> "Simulator":
        if success:
            updated_intervention = intervention.mark_completed(actual_cost)
        else:
            updated_intervention = intervention.mark_failed()

        interventions = [
            updated_intervention if i.id == intervention.id else i
            for i in self.state.interventions
        ]
        interventions.append(updated_intervention) if intervention not in self.state.interventions else None

        return Simulator(SimulatorState(
            merchant=self.state.merchant,
            customers=self.state.customers,
            revenue_events=self.state.revenue_events,
            interventions=interventions,
            recovery_outcomes=self.state.recovery_outcomes,
            current_time=datetime.utcnow(),
        ))

    def record_recovery(
        self,
        revenue_event_id: UUID,
        recovered_amount: Money,
        intervention_id: Optional[UUID] = None,
        is_natural_recovery: Optional[bool] = None,
    ) -> "Simulator":
        if is_natural_recovery is None:
            is_natural_recovery = intervention_id is None
        outcome = RecoveryOutcome.create(
            revenue_event_id=revenue_event_id,
            recovered_amount=recovered_amount,
            intervention_id=intervention_id,
            is_natural_recovery=is_natural_recovery,
        )

        updated_events = []
        for event in self.state.revenue_events:
            if event.id == revenue_event_id:
                if is_natural_recovery:
                    updated_events.append(event.mark_recovered())
                else:
                    updated_events.append(event.mark_recovered())
            else:
                updated_events.append(event)

        return Simulator(SimulatorState(
            merchant=self.state.merchant,
            customers=self.state.customers,
            revenue_events=updated_events,
            interventions=self.state.interventions,
            recovery_outcomes=self.state.recovery_outcomes + [outcome],
            current_time=datetime.utcnow(),
        ))

    def advance_time(self, hours: float) -> "Simulator":
        return Simulator(SimulatorState(
            merchant=self.state.merchant,
            customers=self.state.customers,
            revenue_events=self.state.revenue_events,
            interventions=self.state.interventions,
            recovery_outcomes=self.state.recovery_outcomes,
            current_time=self.state.current_time,
        ))

    def get_failed_events(self) -> List[RevenueEvent]:
        return [e for e in self.state.revenue_events if e.status == RevenueEventStatus.FAILED]

    def get_pending_interventions(self) -> List[Intervention]:
        return [i for i in self.state.interventions if i.status == InterventionStatus.PENDING]

    def get_customer(self, customer_id: UUID) -> Optional[Customer]:
        for c in self.state.customers:
            if c.id == customer_id:
                return c
        return None