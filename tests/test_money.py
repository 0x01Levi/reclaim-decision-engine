import pytest
from decimal import Decimal
from uuid import uuid4

from src.domain import Money


class TestMoney:
    def test_create_from_decimal(self):
        money = Money(Decimal("100.50"))
        assert money.amount == Decimal("100.50")
        assert money.currency == "INR"

    def test_create_from_string(self):
        money = Money("100.50")
        assert money.amount == Decimal("100.50")

    def test_create_from_int(self):
        money = Money(100)
        assert money.amount == Decimal("100")

    def test_create_from_float(self):
        money = Money(100.50)
        assert money.amount == Decimal("100.50")

    def test_zero(self):
        money = Money.zero()
        assert money.amount == Decimal("0")
        assert money.currency == "INR"

    def test_from_paise(self):
        money = Money.from_paise(10050)
        assert money.amount == Decimal("100.50")

    def test_to_paise(self):
        money = Money(Decimal("100.50"))
        assert money.to_paise() == 10050

    def test_add_same_currency(self):
        m1 = Money(Decimal("100.00"))
        m2 = Money(Decimal("50.50"))
        result = m1 + m2
        assert result.amount == Decimal("150.50")

    def test_add_different_currency_raises(self):
        m1 = Money(Decimal("100"), "INR")
        m2 = Money(Decimal("50"), "USD")
        with pytest.raises(ValueError, match="Currency mismatch"):
            m1 + m2

    def test_subtract_valid(self):
        m1 = Money(Decimal("100.00"))
        m2 = Money(Decimal("30.50"))
        result = m1 - m2
        assert result.amount == Decimal("69.50")

    def test_subtract_negative_result(self):
        m1 = Money(Decimal("50.00"))
        m2 = Money(Decimal("100.00"))
        result = m1 - m2
        assert result.amount == Decimal("-50.00")

    def test_multiply_by_decimal(self):
        money = Money(Decimal("100.00"))
        result = money * Decimal("0.1")
        assert result.amount == Decimal("10.00")

    def test_multiply_by_int(self):
        money = Money(Decimal("100.00"))
        result = money * 2
        assert result.amount == Decimal("200.00")

    def test_multiply_by_float(self):
        money = Money(Decimal("100.00"))
        result = money * 0.5
        assert result.amount == Decimal("50.00")

    def test_divide(self):
        money = Money(Decimal("100.00"))
        result = money / 4
        assert result.amount == Decimal("25.00")

    def test_divide_by_zero_raises(self):
        money = Money(Decimal("100.00"))
        with pytest.raises(ZeroDivisionError):
            money / 0

    def test_negative_amount_allowed(self):
        money = Money(Decimal("-10"))
        assert money.amount == Decimal("-10")

    def test_assert_non_negative_raises(self):
        money = Money(Decimal("-10"))
        with pytest.raises(ValueError, match="negative for transactions"):
            money.assert_non_negative()

    def test_invalid_amount_raises(self):
        with pytest.raises(ValueError, match="Invalid monetary amount"):
            Money("not_a_number")

    def test_comparison(self):
        m1 = Money(Decimal("100"))
        m2 = Money(Decimal("200"))
        assert m1 < m2
        assert m2 > m1
        assert m1 <= Money(Decimal("100"))

    def test_str_representation(self):
        money = Money(Decimal("100.50"))
        assert str(money) == "INR 100.50"

    def test_repr(self):
        money = Money(Decimal("100.50"))
        assert "Money(amount=Decimal('100.50')" in repr(money)