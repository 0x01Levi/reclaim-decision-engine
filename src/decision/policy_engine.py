from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from ..domain import Money
from ..domain.enums import DecisionState, InterventionType, PolicyResult

if TYPE_CHECKING:
    from .economic_engine import EconomicResult


@dataclass(frozen=True)
class PolicyConfig:
    min_confidence_threshold: Decimal = Decimal("0.6")
    max_intervention_amount: Money = field(default_factory=lambda: Money(Decimal("10000")))
    max_interventions_per_customer: int = 3
    intervention_cooldown_hours: int = 24
    max_intervention_cost_ratio: Decimal = Decimal("0.5")
    require_economic_viability: bool = True
    blocked_failure_reasons: tuple = ()


@dataclass(frozen=True)
class PolicyContext:
    customer_intervention_count: int
    customer_last_intervention_hours_ago: Optional[float]
    revenue_at_risk: Money
    intervention_type: InterventionType
    intervention_cost: Money
    economic_result: Optional["EconomicResult"] = None


@dataclass(frozen=True)
class PolicyEvaluation:
    result: PolicyResult
    reason: str
    details: dict


class PolicyEngine:
    def __init__(self, config: Optional[PolicyConfig] = None):
        self.config = config or PolicyConfig()

    def evaluate(
        self,
        ai_recommendation: DecisionState,
        confidence: Decimal,
        context: PolicyContext,
    ) -> PolicyEvaluation:
        if ai_recommendation == DecisionState.DO_NOTHING:
            return PolicyEvaluation(
                result=PolicyResult.APPROVE,
                reason="AI recommends no action",
                details={"ai_recommendation": ai_recommendation.value},
            )

        if ai_recommendation == DecisionState.ESCALATE:
            return self._evaluate_escalation(confidence, context)

        if ai_recommendation == DecisionState.WAIT:
            return self._evaluate_wait(confidence, context)

        if ai_recommendation == DecisionState.ACT:
            return self._evaluate_act(confidence, context)

        return PolicyEvaluation(
            result=PolicyResult.REJECT,
            reason=f"Unknown recommendation: {ai_recommendation}",
            details={},
        )

    def _evaluate_act(
        self,
        confidence: Decimal,
        context: PolicyContext,
    ) -> PolicyEvaluation:
        if confidence < self.config.min_confidence_threshold:
            return PolicyEvaluation(
                result=PolicyResult.REJECT,
                reason=f"Confidence {confidence} below threshold {self.config.min_confidence_threshold}",
                details={"confidence": str(confidence), "threshold": str(self.config.min_confidence_threshold)},
            )

        if context.revenue_at_risk > self.config.max_intervention_amount:
            return PolicyEvaluation(
                result=PolicyResult.ESCALATE,
                reason=f"Amount {context.revenue_at_risk} exceeds max intervention limit",
                details={"amount": str(context.revenue_at_risk), "limit": str(self.config.max_intervention_amount)},
            )

        if context.customer_intervention_count >= self.config.max_interventions_per_customer:
            return PolicyEvaluation(
                result=PolicyResult.REJECT,
                reason=f"Customer intervention count {context.customer_intervention_count} exceeds limit",
                details={"count": context.customer_intervention_count, "limit": self.config.max_interventions_per_customer},
            )

        if context.customer_last_intervention_hours_ago is not None:
            if context.customer_last_intervention_hours_ago < self.config.intervention_cooldown_hours:
                return PolicyEvaluation(
                    result=PolicyResult.REJECT,
                    reason=f"Cooldown period not met: {context.customer_last_intervention_hours_ago}h < {self.config.intervention_cooldown_hours}h",
                    details={"hours_since_last": context.customer_last_intervention_hours_ago, "cooldown_hours": self.config.intervention_cooldown_hours},
                )

        cost_ratio = context.intervention_cost.amount / context.revenue_at_risk.amount
        if cost_ratio > self.config.max_intervention_cost_ratio:
            return PolicyEvaluation(
                result=PolicyResult.REJECT,
                reason=f"Intervention cost ratio {cost_ratio:.2%} exceeds max {self.config.max_intervention_cost_ratio:.2%}",
                details={"cost_ratio": str(cost_ratio), "max_ratio": str(self.config.max_intervention_cost_ratio)},
            )

        if self.config.require_economic_viability and context.economic_result:
            if not context.economic_result.is_economically_viable:
                return PolicyEvaluation(
                    result=PolicyResult.REJECT,
                    reason="Intervention not economically viable",
                    details=context.economic_result.to_dict(),
                )

        return PolicyEvaluation(
            result=PolicyResult.APPROVE,
            reason="All policy checks passed",
            details={
                "confidence": str(confidence),
                "intervention_count": context.customer_intervention_count,
                "cost_ratio": str(cost_ratio),
            },
        )

    def _evaluate_wait(
        self,
        confidence: Decimal,
        context: PolicyContext,
    ) -> PolicyEvaluation:
        return PolicyEvaluation(
            result=PolicyResult.APPROVE,
            reason="Wait decision approved",
            details={"confidence": str(confidence)},
        )

    def _evaluate_escalation(
        self,
        confidence: Decimal,
        context: PolicyContext,
    ) -> PolicyEvaluation:
        return PolicyEvaluation(
            result=PolicyResult.APPROVE,
            reason="Escalation approved",
            details={"confidence": str(confidence), "amount": str(context.revenue_at_risk)},
        )