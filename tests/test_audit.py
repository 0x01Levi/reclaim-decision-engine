import pytest
import os
import tempfile
from uuid import uuid4

from src.domain import AuditEvent
from src.audit import AuditStore, create_audit_event


class TestAuditStore:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_audit.db")
        self.store = AuditStore(self.db_path)
        self.merchant_id = uuid4()
        self.entity_id = uuid4()

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_append_and_retrieve(self):
        event = create_audit_event(
            event_type="test_event",
            entity_type="test_entity",
            entity_id=self.entity_id,
            merchant_id=self.merchant_id,
            payload={"key": "value"},
        )

        self.store.append(event)
        retrieved = self.store.get_by_entity("test_entity", self.entity_id)

        assert len(retrieved) == 1
        assert retrieved[0].event_type == "test_event"
        assert retrieved[0].entity_type == "test_entity"
        assert retrieved[0].entity_id == self.entity_id
        assert retrieved[0].merchant_id == self.merchant_id
        assert retrieved[0].payload == {"key": "value"}

    def test_multiple_events_same_entity(self):
        for i in range(3):
            event = create_audit_event(
                event_type=f"event_{i}",
                entity_type="test_entity",
                entity_id=self.entity_id,
                merchant_id=self.merchant_id,
                payload={"sequence": i},
            )
            self.store.append(event)

        retrieved = self.store.get_by_entity("test_entity", self.entity_id)
        assert len(retrieved) == 3
        assert retrieved[0].payload["sequence"] == 0
        assert retrieved[1].payload["sequence"] == 1
        assert retrieved[2].payload["sequence"] == 2

    def test_get_by_merchant(self):
        merchant1 = uuid4()
        merchant2 = uuid4()

        for i in range(3):
            event = create_audit_event(
                event_type=f"event_{i}",
                entity_type="test_entity",
                entity_id=uuid4(),
                merchant_id=merchant1,
                payload={},
            )
            self.store.append(event)

        event = create_audit_event(
            event_type="other_merchant",
            entity_type="test_entity",
            entity_id=uuid4(),
            merchant_id=merchant2,
            payload={},
        )
        self.store.append(event)

        merchant1_events = self.store.get_by_merchant(merchant1)
        merchant2_events = self.store.get_by_merchant(merchant2)

        assert len(merchant1_events) == 3
        assert len(merchant2_events) == 1

    def test_get_by_correlation(self):
        correlation_id = uuid4()

        for i in range(3):
            event = create_audit_event(
                event_type=f"event_{i}",
                entity_type="test_entity",
                entity_id=uuid4(),
                merchant_id=self.merchant_id,
                payload={},
                correlation_id=correlation_id,
            )
            self.store.append(event)

        event = create_audit_event(
            event_type="no_correlation",
            entity_type="test_entity",
            entity_id=uuid4(),
            merchant_id=self.merchant_id,
            payload={},
        )
        self.store.append(event)

        correlated = self.store.get_by_correlation(correlation_id)
        assert len(correlated) == 3

    def test_get_all_limited(self):
        for i in range(10):
            event = create_audit_event(
                event_type=f"event_{i}",
                entity_type="test_entity",
                entity_id=uuid4(),
                merchant_id=self.merchant_id,
                payload={},
            )
            self.store.append(event)

        all_events = self.store.get_all(limit=5)
        assert len(all_events) == 5

    def test_causation_chain(self):
        causation_id = uuid4()
        event = create_audit_event(
            event_type="effect",
            entity_type="test_entity",
            entity_id=self.entity_id,
            merchant_id=self.merchant_id,
            payload={},
            causation_id=causation_id,
        )
        self.store.append(event)

        retrieved = self.store.get_by_entity("test_entity", self.entity_id)
        assert retrieved[0].causation_id == causation_id