from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from ..domain import Money
from ..domain.enums import DecisionState, InterventionType, PolicyResult
from ..domain.models import Customer, Decision, FailureEvent, Merchant, RevenueEvent
from .economic_engine import EconomicInputs, calculate_expected_net_value, estimate_intervention_cost
from .policy_engine import PolicyConfig, PolicyContext, PolicyEngine, PolicyEvaluation


@dataclass(frozen=True)
class DecisionContext:
    merchant: Merchant
    customer: Customer
    revenue_event: RevenueEvent
    failure_event: FailureEvent
    intervention_type: InterventionType
    recovery_probability: Decimal
    ai_recommendation: Optional[DecisionState] = None
    ai_confidence: Optional[Decimal] = None
    ai_reasoning: str = ""


class DecisionEngine:
    def __init__(self, policy_config: Optional[PolicyConfig] = None):
        self.policy_engine = PolicyEngine(policy_config)

    def decide(self, context: DecisionContext) -> Decision:
        recoverable_amount = context.revenue_event.amount
        intervention_cost = estimate_intervention_cost(
            context.intervention_type,
            recoverable_amount,
        )

        economic_inputs = EconomicInputs(
            recovery_probability=context.recovery_probability,
            recoverable_amount=recoverable_amount,
            intervention_cost=intervention_cost,
        )
        economic_result = calculate_expected_net_value(economic_inputs)

        ai_rec = context.ai_recommendation or self._default_recommendation(
            context.recovery_probability,
            economic_result.is_economically_viable,
            context.intervention_type,
        )
        ai_conf = context.ai_confidence or context.recovery_probability
        reasoning = context.ai_reasoning or self._default_reasoning(
            context.recovery_probability,
            economic_result,
        )

        policy_context = PolicyContext(
            customer_intervention_count=context.customer.intervention_count,
            customer_last_intervention_hours_ago=self._hours_since_last_intervention(
                context.customer
            ),
            revenue_at_risk=recoverable_amount,
            intervention_type=context.intervention_type,
            intervention_cost=intervention_cost,
            economic_result=economic_result,
        )

        policy_eval = self.policy_engine.evaluate(ai_rec, ai_conf, policy_context)

        final_state = self._determine_final_state(ai_rec, policy_eval)

        decision = Decision.create(
            revenue_event_id=context.revenue_event.id,
            customer_id=context.customer.id,
            merchant_id=context.merchant.id,
            state=final_state,
            confidence=ai_conf,
            reasoning=reasoning,
            ai_recommendation=ai_rec,
            ai_confidence=ai_conf,
        )

        return decision.with_policy_result(policy_eval.result, policy_eval.reason)

    def _default_recommendation(
        self,
        recovery_probability: Decimal,
        is_economically_viable: bool,
        intervention_type: InterventionType = InterventionType.RETRY_PAYMENT,
    ) -> DecisionState:
        if intervention_type == InterventionType.ESCALATION:
            return DecisionState.ESCALATE
        if not is_economically_viable:
            return DecisionState.DO_NOTHING
        if recovery_probability >= Decimal("0.7"):
            return DecisionState.ACT
        if recovery_probability >= Decimal("0.3"):
            return DecisionState.WAIT
        return DecisionState.DO_NOTHING

    def _default_reasoning(
        self,
        recovery_probability: Decimal,
        economic_result,
    ) -> str:
        return (
            f"Recovery probability: {recovery_probability:.2%}, "
            f"Expected net value: {economic_result.expected_net_value}, "
            f"Economically viable: {economic_result.is_economically_viable}"
        )

    def _hours_since_last_intervention(self, customer: Customer) -> Optional[float]:
        if customer.last_intervention_at is None:
            return None
        from datetime import datetime
        delta = datetime.utcnow() - customer.last_intervention_at
        return delta.total_seconds() / 3600

    def _determine_final_state(
        self,
        ai_recommendation: DecisionState,
        policy_eval: PolicyEvaluation,
    ) -> DecisionState:
        if policy_eval.result == PolicyResult.REJECT:
            if ai_recommendation == DecisionState.ACT:
                return DecisionState.DO_NOTHING
            return ai_recommendation
        if policy_eval.result == PolicyResult.ESCALATE:
            return DecisionState.ESCALATE
        return ai_recommendation