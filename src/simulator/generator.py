import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from ..domain import Money
from ..domain.enums import FailureReason, InterventionType, RevenueEventStatus
from ..domain.models import Customer, FailureEvent, Merchant, RevenueEvent


class SyntheticDataGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self._merchant_id: Optional[UUID] = None

    def generate_merchant(self, name: str = "Test Merchant", risk_tier: str = "STANDARD") -> Merchant:
        merchant = Merchant.create(name=name, email=f"{name.lower().replace(' ', '.')}@example.com", risk_tier=risk_tier)
        self._merchant_id = merchant.id
        return merchant

    def generate_customer(self, merchant_id: UUID) -> Customer:
        return Customer.create(
            merchant_id=merchant_id,
            email=f"customer_{self.rng.randint(1, 10000)}@example.com",
            phone=f"+91{self.rng.randint(7000000000, 9999999999)}",
        )

    def generate_scenario_batch(self, merchant: Merchant, count: int = 100) -> List["Scenario"]:
        scenarios = []
        scenario_types = [
            self._generate_transient_failure,
            self._generate_insufficient_funds,
            self._generate_repeated_failure,
            self._generate_customer_action_required,
            self._generate_natural_recovery,
            self._generate_unrecoverable,
            self._generate_intervention_fatigue,
            self._generate_escalation_case,
        ]

        for i in range(count):
            scenario_type = self.rng.choice(scenario_types)
            scenario = scenario_type(merchant, i)
            scenarios.append(scenario)

        return scenarios

    def _generate_transient_failure(self, merchant: Merchant, index: int) -> "Scenario":
        customer = self.generate_customer(merchant.id)
        amount = Money(Decimal(str(self.rng.uniform(100, 5000))).quantize(Decimal("0.01")))
        revenue_event = RevenueEvent.create(
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount=amount,
            description=f"Subscription payment #{index}",
        )
        failure_event = FailureEvent.create(
            revenue_event_id=revenue_event.id,
            reason=FailureReason.NETWORK_ERROR,
            error_code="NETWORK_TIMEOUT",
            error_message="Payment gateway timeout",
        )
        return Scenario(
            name="transient_failure",
            merchant=merchant,
            customer=customer,
            revenue_event=revenue_event.mark_failed(),
            failure_event=failure_event,
            recovery_probability=Decimal("0.85"),
            intervention_type=InterventionType.RETRY_PAYMENT,
            expected_natural_recovery=True,
        )

    def _generate_insufficient_funds(self, merchant: Merchant, index: int) -> "Scenario":
        customer = self.generate_customer(merchant.id)
        amount = Money(Decimal(str(self.rng.uniform(500, 10000))).quantize(Decimal("0.01")))
        revenue_event = RevenueEvent.create(
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount=amount,
            description=f"EMI payment #{index}",
        )
        failure_event = FailureEvent.create(
            revenue_event_id=revenue_event.id,
            reason=FailureReason.INSUFFICIENT_FUNDS,
            error_code="INSUFFICIENT_FUNDS",
            error_message="Insufficient balance in account",
        )
        return Scenario(
            name="insufficient_funds",
            merchant=merchant,
            customer=customer,
            revenue_event=revenue_event.mark_failed(),
            failure_event=failure_event,
            recovery_probability=Decimal("0.45"),
            intervention_type=InterventionType.CUSTOMER_NOTIFICATION,
            expected_natural_recovery=False,
        )

    def _generate_repeated_failure(self, merchant: Merchant, index: int) -> "Scenario":
        customer = self.generate_customer(merchant.id)
        customer = Customer(
            id=customer.id,
            merchant_id=customer.merchant_id,
            email=customer.email,
            phone=customer.phone,
            created_at=customer.created_at,
            total_lifetime_value=customer.total_lifetime_value,
            intervention_count=3,
            last_intervention_at=datetime.utcnow() - timedelta(hours=6),
        )
        amount = Money(Decimal(str(self.rng.uniform(200, 3000))).quantize(Decimal("0.01")))
        revenue_event = RevenueEvent.create(
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount=amount,
            description=f"Recurring payment #{index}",
        )
        failure_event = FailureEvent.create(
            revenue_event_id=revenue_event.id,
            reason=FailureReason.CARD_DECLINED,
            error_code="CARD_DECLINED",
            error_message="Card declined by issuer",
        )
        failure_event = failure_event.with_retry().with_retry().with_retry()
        return Scenario(
            name="repeated_failure",
            merchant=merchant,
            customer=customer,
            revenue_event=revenue_event.mark_failed(),
            failure_event=failure_event,
            recovery_probability=Decimal("0.25"),
            intervention_type=InterventionType.PAYMENT_METHOD_UPDATE,
            expected_natural_recovery=False,
        )

    def _generate_customer_action_required(self, merchant: Merchant, index: int) -> "Scenario":
        customer = self.generate_customer(merchant.id)
        amount = Money(Decimal(str(self.rng.uniform(1000, 20000))).quantize(Decimal("0.01")))
        revenue_event = RevenueEvent.create(
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount=amount,
            description=f"High-value payment #{index}",
        )
        failure_event = FailureEvent.create(
            revenue_event_id=revenue_event.id,
            reason=FailureReason.CUSTOMER_ACTION_REQUIRED,
            error_code="OTP_REQUIRED",
            error_message="Customer OTP verification required",
        )
        return Scenario(
            name="customer_action_required",
            merchant=merchant,
            customer=customer,
            revenue_event=revenue_event.mark_failed(),
            failure_event=failure_event,
            recovery_probability=Decimal("0.70"),
            intervention_type=InterventionType.CUSTOMER_NOTIFICATION,
            expected_natural_recovery=False,
        )

    def _generate_natural_recovery(self, merchant: Merchant, index: int) -> "Scenario":
        customer = self.generate_customer(merchant.id)
        amount = Money(Decimal(str(self.rng.uniform(50, 1000))).quantize(Decimal("0.01")))
        revenue_event = RevenueEvent.create(
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount=amount,
            description=f"Small payment #{index}",
        )
        failure_event = FailureEvent.create(
            revenue_event_id=revenue_event.id,
            reason=FailureReason.TECHNICAL_FAILURE,
            error_code="TEMPORARY_UNAVAILABLE",
            error_message="Service temporarily unavailable",
        )
        return Scenario(
            name="natural_recovery",
            merchant=merchant,
            customer=customer,
            revenue_event=revenue_event.mark_failed(),
            failure_event=failure_event,
            recovery_probability=Decimal("0.90"),
            intervention_type=InterventionType.RETRY_PAYMENT,
            expected_natural_recovery=True,
        )

    def _generate_unrecoverable(self, merchant: Merchant, index: int) -> "Scenario":
        customer = self.generate_customer(merchant.id)
        amount = Money(Decimal(str(self.rng.uniform(100, 5000))).quantize(Decimal("0.01")))
        revenue_event = RevenueEvent.create(
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount=amount,
            description=f"Failed payment #{index}",
        )
        failure_event = FailureEvent.create(
            revenue_event_id=revenue_event.id,
            reason=FailureReason.FRAUD_SUSPECTED,
            error_code="FRAUD_DETECTED",
            error_message="Transaction flagged as fraudulent",
        )
        return Scenario(
            name="unrecoverable",
            merchant=merchant,
            customer=customer,
            revenue_event=revenue_event.mark_failed(),
            failure_event=failure_event,
            recovery_probability=Decimal("0.02"),
            intervention_type=InterventionType.MANUAL_REVIEW,
            expected_natural_recovery=False,
        )

    def _generate_intervention_fatigue(self, merchant: Merchant, index: int) -> "Scenario":
        customer = self.generate_customer(merchant.id)
        customer = Customer(
            id=customer.id,
            merchant_id=customer.merchant_id,
            email=customer.email,
            phone=customer.phone,
            created_at=customer.created_at,
            total_lifetime_value=customer.total_lifetime_value,
            intervention_count=5,
            last_intervention_at=datetime.utcnow() - timedelta(hours=2),
        )
        amount = Money(Decimal(str(self.rng.uniform(200, 2000))).quantize(Decimal("0.01")))
        revenue_event = RevenueEvent.create(
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount=amount,
            description=f"Fatigue payment #{index}",
        )
        failure_event = FailureEvent.create(
            revenue_event_id=revenue_event.id,
            reason=FailureReason.CARD_EXPIRED,
            error_code="CARD_EXPIRED",
            error_message="Card has expired",
        )
        return Scenario(
            name="intervention_fatigue",
            merchant=merchant,
            customer=customer,
            revenue_event=revenue_event.mark_failed(),
            failure_event=failure_event,
            recovery_probability=Decimal("0.40"),
            intervention_type=InterventionType.PAYMENT_METHOD_UPDATE,
            expected_natural_recovery=False,
        )

    def _generate_escalation_case(self, merchant: Merchant, index: int) -> "Scenario":
        customer = self.generate_customer(merchant.id)
        amount = Money(Decimal(str(self.rng.uniform(50000, 200000))).quantize(Decimal("0.01")))
        revenue_event = RevenueEvent.create(
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount=amount,
            description=f"Enterprise payment #{index}",
        )
        failure_event = FailureEvent.create(
            revenue_event_id=revenue_event.id,
            reason=FailureReason.BANK_ERROR,
            error_code="BANK_DECLINED",
            error_message="Bank declined - requires manual review",
        )
        return Scenario(
            name="escalation_case",
            merchant=merchant,
            customer=customer,
            revenue_event=revenue_event.mark_failed(),
            failure_event=failure_event,
            recovery_probability=Decimal("0.60"),
            intervention_type=InterventionType.ESCALATION,
            expected_natural_recovery=False,
        )


@dataclass(frozen=True)
class Scenario:
    name: str
    merchant: Merchant
    customer: Customer
    revenue_event: RevenueEvent
    failure_event: FailureEvent
    recovery_probability: Decimal
    intervention_type: InterventionType
    expected_natural_recovery: bool


def create_deterministic_batch(seed: int = 42, count: int = 100) -> List[Scenario]:
    generator = SyntheticDataGenerator(seed)
    merchant = generator.generate_merchant()
    return generator.generate_scenario_batch(merchant, count)