from dataclasses import dataclass
from decimal import Decimal
from typing import List
from uuid import UUID

from ..domain import Money
from ..domain.enums import InterventionStatus, RevenueEventStatus
from ..domain.models import Intervention, RecoveryOutcome, RevenueEvent


@dataclass(frozen=True)
class EvaluationResult:
    total_revenue_at_risk: Money
    total_recovered_revenue: Money
    total_intervention_cost: Money
    net_recovered_value: Money
    recovery_rate: Decimal
    intervention_rate: Decimal
    baseline_recovery: Money
    incremental_recovered_value: Money
    roi: Decimal
    total_events: int
    recovered_events: int
    intervened_events: int
    natural_recovery_events: int
    intervention_recovery_events: int

    def to_dict(self) -> dict:
        return {
            "total_revenue_at_risk": str(self.total_revenue_at_risk),
            "total_recovered_revenue": str(self.total_recovered_revenue),
            "total_intervention_cost": str(self.total_intervention_cost),
            "net_recovered_value": str(self.net_recovered_value),
            "recovery_rate": str(self.recovery_rate),
            "intervention_rate": str(self.intervention_rate),
            "baseline_recovery": str(self.baseline_recovery),
            "incremental_recovered_value": str(self.incremental_recovered_value),
            "roi": str(self.roi),
            "total_events": self.total_events,
            "recovered_events": self.recovered_events,
            "intervened_events": self.intervened_events,
            "natural_recovery_events": self.natural_recovery_events,
            "intervention_recovery_events": self.intervention_recovery_events,
        }


def evaluate_batch(
    revenue_events: List[RevenueEvent],
    interventions: List[Intervention],
    recovery_outcomes: List[RecoveryOutcome],
    baseline_recovery_rate: Decimal = Decimal("0.15"),
) -> EvaluationResult:
    failed_events = [e for e in revenue_events if e.status == RevenueEventStatus.FAILED]
    total_events = len(failed_events)

    if total_events == 0:
        return EvaluationResult(
            total_revenue_at_risk=Money.zero(),
            total_recovered_revenue=Money.zero(),
            total_intervention_cost=Money.zero(),
            net_recovered_value=Money.zero(),
            recovery_rate=Decimal("0"),
            intervention_rate=Decimal("0"),
            baseline_recovery=Money.zero(),
            incremental_recovered_value=Money.zero(),
            roi=Decimal("0"),
            total_events=0,
            recovered_events=0,
            intervened_events=0,
            natural_recovery_events=0,
            intervention_recovery_events=0,
        )

    total_revenue_at_risk = Money.zero()
    for event in failed_events:
        total_revenue_at_risk = total_revenue_at_risk + event.amount

    completed_interventions = [i for i in interventions if i.status == InterventionStatus.COMPLETED]
    total_intervention_cost = Money.zero()
    for intervention in completed_interventions:
        total_intervention_cost = total_intervention_cost + intervention.actual_cost

    intervention_recovery_outcomes = [
        o for o in recovery_outcomes if o.intervention_id is not None
    ]
    natural_recovery_outcomes = [
        o for o in recovery_outcomes if o.intervention_id is None
    ]

    total_recovered_revenue = Money.zero()
    for outcome in recovery_outcomes:
        total_recovered_revenue = total_recovered_revenue + outcome.recovered_amount

    intervention_recovered = Money.zero()
    for outcome in intervention_recovery_outcomes:
        intervention_recovered = intervention_recovered + outcome.recovered_amount

    natural_recovered = Money.zero()
    for outcome in natural_recovery_outcomes:
        natural_recovered = natural_recovered + outcome.recovered_amount

    net_recovered_value = total_recovered_revenue - total_intervention_cost

    recovery_rate = (
        Decimal(len(recovery_outcomes)) / Decimal(total_events)
        if total_events > 0 else Decimal("0")
    )

    intervention_rate = (
        Decimal(len(completed_interventions)) / Decimal(total_events)
        if total_events > 0 else Decimal("0")
    )

    baseline_recovery = total_revenue_at_risk * baseline_recovery_rate
    incremental_recovered_value = total_recovered_revenue - baseline_recovery

    roi = (
        (net_recovered_value.amount / total_intervention_cost.amount)
        if total_intervention_cost.amount > 0 else Decimal("0")
    )

    return EvaluationResult(
        total_revenue_at_risk=total_revenue_at_risk,
        total_recovered_revenue=total_recovered_revenue,
        total_intervention_cost=total_intervention_cost,
        net_recovered_value=net_recovered_value,
        recovery_rate=recovery_rate,
        intervention_rate=intervention_rate,
        baseline_recovery=baseline_recovery,
        incremental_recovered_value=incremental_recovered_value,
        roi=roi,
        total_events=total_events,
        recovered_events=len(recovery_outcomes),
        intervened_events=len(completed_interventions),
        natural_recovery_events=len(natural_recovery_outcomes),
        intervention_recovery_events=len(intervention_recovery_outcomes),
    )


def compare_baseline_vs_reclaim(
    baseline_result: EvaluationResult,
    reclaim_result: EvaluationResult,
) -> dict:
    return {
        "revenue_at_risk_baseline": str(baseline_result.total_revenue_at_risk),
        "revenue_at_risk_reclaim": str(reclaim_result.total_revenue_at_risk),
        "recovered_baseline": str(baseline_result.total_recovered_revenue),
        "recovered_reclaim": str(reclaim_result.total_recovered_revenue),
        "net_recovered_baseline": str(baseline_result.net_recovered_value),
        "net_recovered_reclaim": str(reclaim_result.net_recovered_value),
        "incremental_recovered_baseline": str(baseline_result.incremental_recovered_value),
        "incremental_recovered_reclaim": str(reclaim_result.incremental_recovered_value),
        "roi_baseline": str(baseline_result.roi),
        "roi_reclaim": str(reclaim_result.roi),
        "recovery_rate_baseline": str(baseline_result.recovery_rate),
        "recovery_rate_reclaim": str(reclaim_result.recovery_rate),
        "intervention_rate_baseline": str(baseline_result.intervention_rate),
        "intervention_rate_reclaim": str(reclaim_result.intervention_rate),
        "net_improvement": str(reclaim_result.net_recovered_value - baseline_result.net_recovered_value),
        "incremental_improvement": str(
            reclaim_result.incremental_recovered_value - baseline_result.incremental_recovered_value
        ),
    }