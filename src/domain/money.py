from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Union


@dataclass(frozen=True, order=True)
class Money:
    amount: Decimal
    currency: str = "INR"

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            try:
                object.__setattr__(self, "amount", Decimal(str(self.amount)))
            except (InvalidOperation, TypeError) as e:
                raise ValueError(f"Invalid monetary amount: {self.amount}") from e

        if not self.currency or not isinstance(self.currency, str):
            raise ValueError("Currency must be a non-empty string")

    def assert_non_negative(self) -> "Money":
        """Assert this money amount is non-negative (for actual transactions)."""
        if self.amount < 0:
            raise ValueError("Monetary amount cannot be negative for transactions")
        return self

    @classmethod
    def zero(cls, currency: str = "INR") -> "Money":
        return cls(Decimal("0"), currency)

    @classmethod
    def from_paise(cls, paise: int, currency: str = "INR") -> "Money":
        return cls(Decimal(paise) / Decimal("100"), currency)

    def to_paise(self) -> int:
        return int((self.amount * Decimal("100")).quantize(Decimal("1")))

    def __add__(self, other: "Money") -> "Money":
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Union[int, float, Decimal]) -> "Money":
        if isinstance(factor, float):
            factor = Decimal(str(factor))
        elif isinstance(factor, int):
            factor = Decimal(factor)
        return Money(self.amount * factor, self.currency)

    def __truediv__(self, divisor: Union[int, float, Decimal]) -> "Money":
        if isinstance(divisor, float):
            divisor = Decimal(str(divisor))
        elif isinstance(divisor, int):
            divisor = Decimal(divisor)
        if divisor == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return Money(self.amount / divisor, self.currency)

    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)

    def _check_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"

    def __repr__(self) -> str:
        return f"Money(amount=Decimal('{self.amount}'), currency='{self.currency}')"