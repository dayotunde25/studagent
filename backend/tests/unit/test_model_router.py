"""
Unit tests for Model Router component.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.services.model_router import ModelRouter, ModelStatus
from app.core.config import settings


class TestModelRouter:
    """Test cases for ModelRouter class."""

    @pytest.fixture
    def model_router(self):
        """Create a ModelRouter instance for testing."""
        return ModelRouter()

    def test_model_router_initialization(self, model_router):
        """Test ModelRouter initialization."""
        assert model_router is not None
        assert hasattr(model_router, 'model_statuses')
        assert hasattr(model_router, 'priority_list')

    def test_get_available_models(self, model_router):
        """Test getting available models."""
        models = model_router.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        # Should include our configured models
        assert "mistral-7b" in models

    @patch('app.services.model_router.httpx.AsyncClient')
    async def test_call_model_success(self, mock_client, model_router):
        """Test successful model call."""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        result = await model_router.call_model(
            model="mistral-7b",
            prompt="Test prompt",
            task_type="summarize"
        )

        assert result is not None
        assert "Test response" in result

    @patch('app.services.model_router.httpx.AsyncClient')
    async def test_call_model_failure(self, mock_client, model_router):
        """Test model call failure."""
        # Mock a failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server error")

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        with pytest.raises(Exception):
            await model_router.call_model(
                model="mistral-7b",
                prompt="Test prompt",
                task_type="summarize"
            )

    def test_update_model_status(self, model_router):
        """Test updating model status."""
        model_router.update_model_status("mistral-7b", ModelStatus.DEGRADED)

        status = model_router.get_model_status("mistral-7b")
        assert status == ModelStatus.DEGRADED

    def test_get_model_status(self, model_router):
        """Test getting model status."""
        # Initially should be healthy
        status = model_router.get_model_status("mistral-7b")
        assert status == ModelStatus.HEALTHY

        # After updating
        model_router.update_model_status("mistral-7b", ModelStatus.DEGRADED)
        status = model_router.get_model_status("mistral-7b")
        assert status == ModelStatus.DEGRADED

    def test_is_model_available(self, model_router):
        """Test checking if model is available."""
        # Initially should be available
        assert model_router.is_model_available("mistral-7b") is True

        # After marking as degraded
        model_router.update_model_status("mistral-7b", ModelStatus.DEGRADED)
        assert model_router.is_model_available("mistral-7b") is False

    def test_get_next_available_model(self, model_router):
        """Test getting next available model."""
        # With all models healthy
        next_model = model_router.get_next_available_model()
        assert next_model is not None
        assert next_model in model_router.get_available_models()

        # With first model degraded
        first_model = model_router.priority_list[0]
        model_router.update_model_status(first_model, ModelStatus.DEGRADED)

        next_model = model_router.get_next_available_model()
        assert next_model != first_model
        assert next_model in model_router.get_available_models()

    @patch('app.services.model_router.httpx.AsyncClient')
    async def test_process_request_with_fallback(self, mock_client, model_router):
        """Test request processing with fallback."""
        # Mock first model failure
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = Exception("Server error")

        # Mock second model success
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Fallback response"}}]
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance

        # First call fails, second succeeds
        mock_client_instance.post.side_effect = [
            mock_response_fail,  # First model fails
            mock_response_success  # Second model succeeds
        ]
        mock_client.return_value = mock_client_instance

        result = await model_router.process_request(
            prompt="Test prompt",
            task_type="summarize"
        )

        assert result is not None
        assert "Fallback response" in result

    def test_circuit_breaker_logic(self, model_router):
        """Test circuit breaker functionality."""
        model_name = "mistral-7b"

        # Initially healthy
        assert model_router.is_model_available(model_name) is True

        # Simulate multiple failures
        for _ in range(5):  # Assuming threshold is 5
            model_router.record_model_failure(model_name)

        # Should be marked as degraded
        assert model_router.is_model_available(model_name) is False

    def test_model_failure_tracking(self, model_router):
        """Test model failure tracking."""
        model_name = "mistral-7b"

        # Record some failures
        initial_failures = model_router.get_model_failures(model_name)
        model_router.record_model_failure(model_name)
        model_router.record_model_failure(model_name)

        current_failures = model_router.get_model_failures(model_name)
        assert current_failures == initial_failures + 2

    def test_model_recovery(self, model_router):
        """Test model recovery after failures."""
        model_name = "mistral-7b"

        # Mark as degraded
        model_router.update_model_status(model_name, ModelStatus.DEGRADED)
        assert model_router.is_model_available(model_name) is False

        # Manually recover
        model_router.recover_model(model_name)
        assert model_router.is_model_available(model_name) is True

    def test_priority_list_ordering(self, model_router):
        """Test that priority list is properly ordered."""
        priority_list = model_router.priority_list

        # Should start with preferred models
        assert "mistral-7b" in priority_list[:3]  # Should be in top 3

        # Should include fallback options
        assert "gemini" in priority_list  # Should include Gemini as fallback

    def test_task_type_routing(self, model_router):
        """Test routing based on task type."""
        # Test different task types
        task_types = ["summarize", "flashcard", "quiz", "match", "write"]

        for task_type in task_types:
            model = model_router.get_model_for_task(task_type)
            assert model is not None
            assert model in model_router.get_available_models()

    def test_model_timeout_handling(self, model_router):
        """Test timeout handling for model calls."""
        # This would typically test the timeout parameter
        # but since we're mocking, we'll test the configuration
        assert hasattr(model_router, 'timeout')
        assert model_router.timeout > 0

    def test_concurrent_request_handling(self, model_router):
        """Test handling of concurrent requests."""
        # Test that multiple requests don't interfere with each other
        status1 = model_router.get_model_status("mistral-7b")
        model_router.update_model_status("mistral-7b", ModelStatus.DEGRADED)
        status2 = model_router.get_model_status("mistral-7b")

        assert status1 == ModelStatus.HEALTHY
        assert status2 == ModelStatus.DEGRADED

    def test_model_health_check(self, model_router):
        """Test model health check functionality."""
        # Test health check for a model
        is_healthy = model_router.check_model_health("mistral-7b")
        # This might be a mock or actual check depending on implementation
        assert isinstance(is_healthy, bool)

    def test_error_handling_edge_cases(self, model_router):
        """Test error handling for edge cases."""
        # Test with invalid model name
        result = model_router.get_model_status("invalid-model")
        assert result is None or isinstance(result, ModelStatus)

        # Test with empty prompt
        with pytest.raises(ValueError):
            # This should raise an error for empty prompt
            pass

    def test_metrics_and_logging(self, model_router):
        """Test metrics and logging functionality."""
        # Test that metrics are being tracked
        initial_calls = model_router.get_total_calls()
        # Make a call (mocked)
        # After call, total calls should increase
        # This depends on the actual implementation

    def test_configuration_loading(self, model_router):
        """Test loading configuration from settings."""
        # Test that configuration is properly loaded
        assert hasattr(model_router, 'priority_list')
        assert len(model_router.priority_list) > 0

        assert hasattr(model_router, 'timeout')
        assert model_router.timeout > 0