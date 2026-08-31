import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from ..domain import AuditEvent


class AuditStore:
    def __init__(self, db_path: str = "data/audit.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    merchant_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    correlation_id TEXT,
                    causation_id TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_entity
                ON audit_events(entity_type, entity_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_merchant
                ON audit_events(merchant_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_events(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_correlation
                ON audit_events(correlation_id)
            """)

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def append(self, event: AuditEvent) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (id, event_type, entity_type, entity_id, merchant_id, payload, timestamp, correlation_id, causation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event.id),
                    event.event_type,
                    event.entity_type,
                    str(event.entity_id),
                    str(event.merchant_id),
                    json.dumps(event.payload, default=str),
                    event.timestamp.isoformat(),
                    str(event.correlation_id) if event.correlation_id else None,
                    str(event.causation_id) if event.causation_id else None,
                ),
            )

    def get_by_entity(self, entity_type: str, entity_id: UUID) -> List[AuditEvent]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_events WHERE entity_type = ? AND entity_id = ? ORDER BY timestamp",
                (entity_type, str(entity_id)),
            ).fetchall()
            return [self._row_to_event(row) for row in rows]

    def get_by_merchant(self, merchant_id: UUID, limit: int = 100) -> List[AuditEvent]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_events WHERE merchant_id = ? ORDER BY timestamp DESC LIMIT ?",
                (str(merchant_id), limit),
            ).fetchall()
            return [self._row_to_event(row) for row in rows]

    def get_by_correlation(self, correlation_id: UUID) -> List[AuditEvent]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_events WHERE correlation_id = ? ORDER BY timestamp",
                (str(correlation_id),),
            ).fetchall()
            return [self._row_to_event(row) for row in rows]

    def get_all(self, limit: int = 1000) -> List[AuditEvent]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._row_to_event(row) for row in rows]

    def _row_to_event(self, row: sqlite3.Row) -> AuditEvent:
        return AuditEvent(
            id=UUID(row["id"]),
            event_type=row["event_type"],
            entity_type=row["entity_type"],
            entity_id=UUID(row["entity_id"]),
            merchant_id=UUID(row["merchant_id"]),
            payload=json.loads(row["payload"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            correlation_id=UUID(row["correlation_id"]) if row["correlation_id"] else None,
            causation_id=UUID(row["causation_id"]) if row["causation_id"] else None,
        )


def create_audit_event(
    event_type: str,
    entity_type: str,
    entity_id: UUID,
    merchant_id: UUID,
    payload: dict,
    correlation_id: Optional[UUID] = None,
    causation_id: Optional[UUID] = None,
) -> AuditEvent:
    return AuditEvent.create(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        merchant_id=merchant_id,
        payload=payload,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )