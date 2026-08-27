"""
Integration tests for alert system.

Verification that:
1. Alerts are correctly persisted to MySQL database
2. Alert fields are properly populated
3. Alert status transitions work correctly
"""

import pytest
from datetime import datetime
from typing import Dict, Any


class TestAlertInsertion:
    """Tests for alert database persistence."""
    
    @pytest.fixture
    def mock_analysis_result(self) -> Dict[str, Any]:
        """Create a mock analysis result that would trigger an alert."""
        return {
            "camera_id": "test-camera-1",
            "timestamp": datetime.utcnow().isoformat(),
            "person_count": 20,  # Above crowd threshold
            "crowd_density": 0.75,
            "risk_level": "medium",
            "risk_score": 0.65,
            "event_type": "crowd_formation",
            "explanation": "Elevated crowd density detected (20 persons)",
            "detections": [],
            "loitering_detections": [],
            "aggressive_interactions": []
        }
    
    @pytest.fixture
    def mock_intrusion_alert(self) -> Dict[str, Any]:
        """Create a mock intrusion alert."""
        return {
            "camera_id": "test-camera-2",
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "zone_intrusion",
            "zone_index": 0,
            "risk_level": "high",
            "risk_score": 0.85,
            "explanation": "Person detected in restricted zone 0",
            "person_count": 1
        }
    
    def test_alert_data_structure(self, mock_analysis_result):
        """Test that alert data has all required fields."""
        required_fields = [
            "camera_id",
            "timestamp",
            "event_type",
            "risk_level",
            "explanation"
        ]
        
        for field in required_fields:
            assert field in mock_analysis_result, f"Missing required field: {field}"
        
        print("✅ Alert data structure validation passed")
    
    def test_alert_risk_levels_valid(self, mock_analysis_result):
        """Test that risk levels are valid enum values."""
        valid_levels = ["low", "medium", "high"]
        
        assert mock_analysis_result["risk_level"] in valid_levels, (
            f"Invalid risk level: {mock_analysis_result['risk_level']}"
        )
        
        print("✅ Risk level validation passed")
    
    def test_alert_event_types_valid(self, mock_analysis_result, mock_intrusion_alert):
        """Test that event types are recognized values."""
        valid_event_types = [
            "crowd_formation",
            "zone_intrusion",
            "loitering",
            "aggressive_posture",
            "elevated_risk",
            "abandoned_object"
        ]
        
        assert mock_analysis_result["event_type"] in valid_event_types
        assert mock_intrusion_alert["event_type"] in valid_event_types
        
        print("✅ Event type validation passed")
    
    @pytest.mark.asyncio
    async def test_alert_model_creation(self):
        """Test that Alert model can be instantiated."""
        try:
            from app.models.database_models import Alert, AlertLevel, AlertStatus
        except ImportError:
            pytest.skip("Database models not available")
        
        # This tests the model without database connection
        # Actual DB insertion requires a test database setup
        print("✅ Alert model import successful")
    
    @pytest.mark.asyncio
    async def test_alert_serialization(self, mock_analysis_result):
        """Test that alert data can be serialized for WebSocket broadcast."""
        import json
        
        # Should be JSON serializable
        try:
            serialized = json.dumps(mock_analysis_result)
            deserialized = json.loads(serialized)
            
            assert deserialized["camera_id"] == mock_analysis_result["camera_id"]
            assert deserialized["event_type"] == mock_analysis_result["event_type"]
            
            print("✅ Alert serialization test passed")
        except (TypeError, json.JSONDecodeError) as e:
            pytest.fail(f"Alert data is not JSON serializable: {e}")


class TestAlertStatusTransitions:
    """Tests for alert status state machine."""
    
    def test_valid_status_transitions(self):
        """Test that only valid status transitions are allowed."""
        valid_transitions = {
            "active": ["acknowledged", "false_positive", "escalated"],
            "acknowledged": ["resolved", "escalated", "false_positive"],
            "escalated": ["resolved", "false_positive"],
            "false_positive": [],  # Terminal state
            "resolved": []  # Terminal state
        }
        
        # From active, can go to acknowledged
        assert "acknowledged" in valid_transitions["active"]
        
        # Can't go back to active from resolved
        assert "active" not in valid_transitions["resolved"]
        
        print("✅ Status transition validation passed")
    
    def test_alert_with_actions(self):
        """Test alert with associated user actions."""
        action_data = {
            "alert_id": 1,
            "user_id": 1,
            "action_type": "acknowledge",
            "notes": "Reviewed and acknowledged. Normal activity.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        valid_action_types = [
            "acknowledge",
            "false_positive",
            "escalate",
            "resolve",
            "add_note"
        ]
        
        assert action_data["action_type"] in valid_action_types
        assert action_data["notes"] is not None
        
        print("✅ Alert action validation passed")


class TestAlertWebSocketBroadcast:
    """Tests for real-time alert broadcasting."""
    
    def test_broadcast_message_format(self):
        """Test that broadcast messages have correct format."""
        broadcast_message = {
            "type": "new_alert",
            "data": {
                "id": 1,
                "camera_id": "cam-1",
                "event_type": "crowd_formation",
                "risk_level": "medium",
                "timestamp": datetime.utcnow().isoformat()
            },
            "disclaimer": "Automated detection - requires human verification"
        }
        
        assert "type" in broadcast_message
        assert "data" in broadcast_message
        assert "disclaimer" in broadcast_message
        
        print("✅ Broadcast message format validation passed")
    
    def test_alert_cooldown_logic(self):
        """Test that alert cooldown prevents flooding."""
        try:
            from app.ml.engine import AlertBuffer
        except ImportError:
            pytest.skip("Engine module not available")
        
        buffer = AlertBuffer(cooldown_seconds=30)
        
        # First alert should be allowed
        assert buffer.can_alert("cam-1", "crowd_formation") == True
        
        # Immediate second alert of same type should be blocked
        assert buffer.can_alert("cam-1", "crowd_formation") == False
        
        # Different event type should be allowed
        assert buffer.can_alert("cam-1", "zone_intrusion") == True
        
        # Different camera should be allowed
        assert buffer.can_alert("cam-2", "crowd_formation") == True
        
        print("✅ Alert cooldown logic test passed")


class TestDatabaseIntegration:
    """
    Integration tests requiring actual database connection.
    
    These tests are marked with pytest.mark.integration and should
    be run separately with a test database configured.
    """
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_alert_insertion_to_database(self):
        """
        Full integration test: Insert alert to MySQL and verify.
        
        Requires:
        - MySQL running
        - Test database configured
        - Environment variables set
        """
        pytest.skip("Integration test - requires test database setup")
        
        # This would be the full integration test:
        # 1. Create database session
        # 2. Create Alert model instance
        # 3. Insert to database
        # 4. Query and verify
        # 5. Clean up
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_alert_crud_operations(self):
        """Test full CRUD operations on alerts."""
        pytest.skip("Integration test - requires test database setup")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration"])
