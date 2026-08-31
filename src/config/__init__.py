import os
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from ..domain import Money


@dataclass(frozen=True)
class Config:
    database_path: str = field(default_factory=lambda: os.getenv("RECLAIM_DB_PATH", "data/reclaim.db"))
    audit_database_path: str = field(default_factory=lambda: os.getenv("RECLAIM_AUDIT_DB_PATH", "data/audit.db"))
    api_host: str = field(default_factory=lambda: os.getenv("RECLAIM_API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(os.getenv("RECLAIM_API_PORT", "8000")))
    log_level: str = field(default_factory=lambda: os.getenv("RECLAIM_LOG_LEVEL", "INFO"))
    environment: str = field(default_factory=lambda: os.getenv("RECLAIM_ENV", "development"))

    min_confidence_threshold: Decimal = Decimal("0.6")
    max_intervention_amount: Money = field(default_factory=lambda: Money(Decimal("10000")))
    max_interventions_per_customer: int = 3
    intervention_cooldown_hours: int = 24
    max_intervention_cost_ratio: Decimal = Decimal("0.5")
    require_economic_viability: bool = True
    baseline_recovery_rate: Decimal = Decimal("0.15")


def load_config() -> Config:
    return Config()


DEFAULT_CONFIG = load_config()