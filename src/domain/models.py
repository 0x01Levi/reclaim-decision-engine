from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from .enums import (
    DecisionState,
    FailureReason,
    InterventionStatus,
    InterventionType,
    PolicyResult,
    RevenueEventStatus,
)
from .money import Money


@dataclass(frozen=True)
class Merchant:
    id: UUID
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    risk_tier: str = "STANDARD"
    max_intervention_amount: Money = field(default_factory=lambda: Money(Decimal("10000")))

    @classmethod
    def create(cls, name: str, email: str, risk_tier: str = "STANDARD") -> "Merchant":
        return cls(
            id=uuid4(),
            name=name,
            email=email,
            risk_tier=risk_tier,
        )


@dataclass(frozen=True)
class Customer:
    id: UUID
    merchant_id: UUID
    email: str
    phone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    total_lifetime_value: Money = field(default_factory=lambda: Money.zero())
    intervention_count: int = 0
    last_intervention_at: Optional[datetime] = None

    @classmethod
    def create(cls, merchant_id: UUID, email: str, phone: Optional[str] = None) -> "Customer":
        return cls(
            id=uuid4(),
            merchant_id=merchant_id,
            email=email,
            phone=phone,
        )


@dataclass(frozen=True)
class RevenueEvent:
    id: UUID
    merchant_id: UUID
    customer_id: UUID
    amount: Money
    description: str
    status: RevenueEventStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    external_payment_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        merchant_id: UUID,
        customer_id: UUID,
        amount: Money,
        description: str,
        external_payment_id: Optional[str] = None,
    ) -> "RevenueEvent":
        return cls(
            id=uuid4(),
            merchant_id=merchant_id,
            customer_id=customer_id,
            amount=amount,
            description=description,
            status=RevenueEventStatus.PENDING,
            external_payment_id=external_payment_id,
        )

    def mark_failed(self) -> "RevenueEvent":
        return RevenueEvent(
            id=self.id,
            merchant_id=self.merchant_id,
            customer_id=self.customer_id,
            amount=self.amount,
            description=self.description,
            status=RevenueEventStatus.FAILED,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            external_payment_id=self.external_payment_id,
            metadata=self.metadata,
        )

    def mark_recovered(self) -> "RevenueEvent":
        return RevenueEvent(
            id=self.id,
            merchant_id=self.merchant_id,
            customer_id=self.customer_id,
            amount=self.amount,
            description=self.description,
            status=RevenueEventStatus.RECOVERED,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            external_payment_id=self.external_payment_id,
            metadata=self.metadata,
        )

    def mark_unrecoverable(self) -> "RevenueEvent":
        return RevenueEvent(
            id=self.id,
            merchant_id=self.merchant_id,
            customer_id=self.customer_id,
            amount=self.amount,
            description=self.description,
            status=RevenueEventStatus.UNRECOVERABLE,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            external_payment_id=self.external_payment_id,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class FailureEvent:
    id: UUID
    revenue_event_id: UUID
    reason: FailureReason
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        revenue_event_id: UUID,
        reason: FailureReason,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> "FailureEvent":
        return cls(
            id=uuid4(),
            revenue_event_id=revenue_event_id,
            reason=reason,
            error_code=error_code,
            error_message=error_message,
        )

    def with_retry(self) -> "FailureEvent":
        return FailureEvent(
            id=self.id,
            revenue_event_id=self.revenue_event_id,
            reason=self.reason,
            error_code=self.error_code,
            error_message=self.error_message,
            occurred_at=self.occurred_at,
            retry_count=self.retry_count + 1,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class Intervention:
    id: UUID
    revenue_event_id: UUID
    customer_id: UUID
    merchant_id: UUID
    type: InterventionType
    status: InterventionStatus
    estimated_cost: Money
    actual_cost: Money = field(default_factory=lambda: Money.zero())
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    idempotency_key: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        revenue_event_id: UUID,
        customer_id: UUID,
        merchant_id: UUID,
        type: InterventionType,
        estimated_cost: Money,
    ) -> "Intervention":
        return cls(
            id=uuid4(),
            revenue_event_id=revenue_event_id,
            customer_id=customer_id,
            merchant_id=merchant_id,
            type=type,
            status=InterventionStatus.PENDING,
            estimated_cost=estimated_cost,
        )

    def mark_executing(self) -> "Intervention":
        return Intervention(
            id=self.id,
            revenue_event_id=self.revenue_event_id,
            customer_id=self.customer_id,
            merchant_id=self.merchant_id,
            type=self.type,
            status=InterventionStatus.EXECUTING,
            estimated_cost=self.estimated_cost,
            actual_cost=self.actual_cost,
            created_at=self.created_at,
            executed_at=datetime.utcnow(),
            completed_at=self.completed_at,
            idempotency_key=self.idempotency_key,
            metadata=self.metadata,
        )

    def mark_completed(self, actual_cost: Money) -> "Intervention":
        return Intervention(
            id=self.id,
            revenue_event_id=self.revenue_event_id,
            customer_id=self.customer_id,
            merchant_id=self.merchant_id,
            type=self.type,
            status=InterventionStatus.COMPLETED,
            estimated_cost=self.estimated_cost,
            actual_cost=actual_cost,
            created_at=self.created_at,
            executed_at=self.executed_at,
            completed_at=datetime.utcnow(),
            idempotency_key=self.idempotency_key,
            metadata=self.metadata,
        )

    def mark_failed(self) -> "Intervention":
        return Intervention(
            id=self.id,
            revenue_event_id=self.revenue_event_id,
            customer_id=self.customer_id,
            merchant_id=self.merchant_id,
            type=self.type,
            status=InterventionStatus.FAILED,
            estimated_cost=self.estimated_cost,
            actual_cost=self.actual_cost,
            created_at=self.created_at,
            executed_at=self.executed_at,
            completed_at=datetime.utcnow(),
            idempotency_key=self.idempotency_key,
            metadata=self.metadata,
        )

    def mark_skipped(self) -> "Intervention":
        return Intervention(
            id=self.id,
            revenue_event_id=self.revenue_event_id,
            customer_id=self.customer_id,
            merchant_id=self.merchant_id,
            type=self.type,
            status=InterventionStatus.SKIPPED,
            estimated_cost=self.estimated_cost,
            actual_cost=self.actual_cost,
            created_at=self.created_at,
            executed_at=self.executed_at,
            completed_at=datetime.utcnow(),
            idempotency_key=self.idempotency_key,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class RecoveryOutcome:
    id: UUID
    revenue_event_id: UUID
    intervention_id: Optional[UUID]
    recovered_amount: Money
    recovered_at: datetime = field(default_factory=datetime.utcnow)
    is_natural_recovery: bool = False
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        revenue_event_id: UUID,
        recovered_amount: Money,
        intervention_id: Optional[UUID] = None,
        is_natural_recovery: bool = False,
    ) -> "RecoveryOutcome":
        return cls(
            id=uuid4(),
            revenue_event_id=revenue_event_id,
            intervention_id=intervention_id,
            recovered_amount=recovered_amount,
            is_natural_recovery=is_natural_recovery,
        )


@dataclass(frozen=True)
class Decision:
    id: UUID
    revenue_event_id: UUID
    customer_id: UUID
    merchant_id: UUID
    state: DecisionState
    confidence: Decimal
    reasoning: str
    ai_recommendation: Optional[DecisionState] = None
    ai_confidence: Optional[Decimal] = None
    policy_result: Optional[PolicyResult] = None
    policy_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        revenue_event_id: UUID,
        customer_id: UUID,
        merchant_id: UUID,
        state: DecisionState,
        confidence: Decimal,
        reasoning: str,
        ai_recommendation: Optional[DecisionState] = None,
        ai_confidence: Optional[Decimal] = None,
    ) -> "Decision":
        return cls(
            id=uuid4(),
            revenue_event_id=revenue_event_id,
            customer_id=customer_id,
            merchant_id=merchant_id,
            state=state,
            confidence=confidence,
            reasoning=reasoning,
            ai_recommendation=ai_recommendation,
            ai_confidence=ai_confidence,
        )

    def with_policy_result(self, policy_result: PolicyResult, policy_reason: str) -> "Decision":
        return Decision(
            id=self.id,
            revenue_event_id=self.revenue_event_id,
            customer_id=self.customer_id,
            merchant_id=self.merchant_id,
            state=self.state,
            confidence=self.confidence,
            reasoning=self.reasoning,
            ai_recommendation=self.ai_recommendation,
            ai_confidence=self.ai_confidence,
            policy_result=policy_result,
            policy_reason=policy_reason,
            created_at=self.created_at,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class AuditEvent:
    id: UUID
    event_type: str
    entity_type: str
    entity_id: UUID
    merchant_id: UUID
    payload: dict
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None

    @classmethod
    def create(
        cls,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        merchant_id: UUID,
        payload: dict,
        correlation_id: Optional[UUID] = None,
        causation_id: Optional[UUID] = None,
    ) -> "AuditEvent":
        return cls(
            id=uuid4(),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            merchant_id=merchant_id,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )