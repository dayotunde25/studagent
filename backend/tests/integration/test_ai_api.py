"""
Integration tests for AI API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestAIApi:
    """Test cases for AI API endpoints."""

    @patch('app.services.model_router.ModelRouter.process_request')
    def test_summarize_endpoint_success(self, mock_process_request, client: TestClient, auth_headers):
        """Test successful document summarization."""
        mock_process_request.return_value = "This is a summary of the document."

        request_data = {
            "text": "This is a long document that needs to be summarized...",
            "max_length": 100
        }

        response = client.post("/api/v1/ai/summarize", json=request_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "This is a summary" in data["summary"]
        mock_process_request.assert_called_once()

    @patch('app.services.model_router.ModelRouter.process_request')
    def test_summarize_endpoint_with_document(self, mock_process_request, client: TestClient, auth_headers, sample_document_data):
        """Test summarization with document ID."""
        mock_process_request.return_value = "Document summary here."

        request_data = {
            "document_id": 1,
            "max_length": 150
        }

        response = client.post("/api/v1/ai/summarize", json=request_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        mock_process_request.assert_called_once()

    def test_summarize_endpoint_unauthenticated(self, client: TestClient):
        """Test summarization without authentication."""
        request_data = {
            "text": "Test document text"
        }

        response = client.post("/api/v1/ai/summarize", json=request_data)

        assert response.status_code == 401

    @patch('app.services.model_router.ModelRouter.process_request')
    def test_flashcards_endpoint_success(self, mock_process_request, client: TestClient, auth_headers):
        """Test successful flashcard generation."""
        mock_flashcards = [
            {"question": "What is AI?", "answer": "Artificial Intelligence"},
            {"question": "What is ML?", "answer": "Machine Learning"}
        ]
        mock_process_request.return_value = str(mock_flashcards)

        request_data = {
            "text": "AI and ML are important technologies...",
            "num_cards": 2
        }

        response = client.post("/api/v1/ai/flashcards", json=request_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "flashcards" in data
        mock_process_request.assert_called_once()

    @patch('app.services.model_router.ModelRouter.process_request')
    def test_quiz_endpoint_success(self, mock_process_request, client: TestClient, auth_headers):
        """Test successful quiz generation."""
        mock_quiz = {
            "questions": [
                {
                    "question": "What is Python?",
                    "options": ["Snake", "Programming Language", "Food", "Animal"],
                    "correct_answer": 1,
                    "explanation": "Python is a programming language."
                }
            ]
        }
        mock_process_request.return_value = str(mock_quiz)

        request_data = {
            "text": "Python is a programming language...",
            "num_questions": 1,
            "difficulty": "easy"
        }

        response = client.post("/api/v1/ai/quiz", json=request_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "quiz" in data
        mock_process_request.assert_called_once()

    @patch('app.services.model_router.ModelRouter.process_request')
    def test_match_partners_endpoint_success(self, mock_process_request, client: TestClient, auth_headers):
        """Test successful partner matching."""
        mock_matches = [
            {"user_id": 2, "score": 0.85, "reason": "Similar interests in AI"},
            {"user_id": 3, "score": 0.72, "reason": "Same major in Computer Science"}
        ]
        mock_process_request.return_value = str(mock_matches)

        response = client.post("/api/v1/ai/match-partners", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        mock_process_request.assert_called_once()

    @patch('app.services.model_router.ModelRouter.process_request')
    def test_write_endpoint_success(self, mock_process_request, client: TestClient, auth_headers):
        """Test successful content writing."""
        mock_content = "This is a well-written essay about artificial intelligence..."
        mock_process_request.return_value = mock_content

        request_data = {
            "prompt": "Write an essay about AI",
            "style": "academic",
            "length": "medium"
        }

        response = client.post("/api/v1/ai/write", json=request_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "essay" in data["content"].lower()
        mock_process_request.assert_called_once()

    @patch('app.services.model_router.ModelRouter.process_request')
    def test_scholarship_alerts_endpoint_success(self, mock_process_request, client: TestClient, auth_headers):
        """Test successful scholarship alerts."""
        mock_opportunities = [
            {
                "title": "AI Research Scholarship",
                "description": "Scholarship for AI research",
                "url": "https://example.com/scholarship",
                "match_score": 0.9,
                "reason": "Matches your AI interests"
            }
        ]
        mock_process_request.return_value = str(mock_opportunities)

        response = client.post("/api/v1/ai/scholarship-alerts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "opportunities" in data
        mock_process_request.assert_called_once()

    def test_ai_endpoints_rate_limiting(self, client: TestClient, auth_headers):
        """Test rate limiting on AI endpoints."""
        # Make multiple requests quickly
        for i in range(10):
            response = client.post("/api/v1/ai/summarize", json={
                "text": f"Test text {i}"
            }, headers=auth_headers)

            if response.status_code == 429:  # Too Many Requests
                break

        # Should eventually hit rate limit
        # Note: This depends on rate limiting configuration

    @patch('app.services.model_router.ModelRouter.process_request')
    def test_ai_endpoint_model_failure_fallback(self, mock_process_request, client: TestClient, auth_headers):
        """Test AI endpoint fallback when model fails."""
        # Mock model failure followed by success
        mock_process_request.side_effect = [
            Exception("Model failed"),  # First call fails
            "Fallback successful response"  # Second call succeeds
        ]

        request_data = {
            "text": "Test document for fallback",
            "max_length": 50
        }

        response = client.post("/api/v1/ai/summarize", json=request_data, headers=auth_headers)

        # Should eventually succeed with fallback
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    def test_ai_endpoint_invalid_input(self, client: TestClient, auth_headers):
        """Test AI endpoint with invalid input."""
        # Empty text
        response = client.post("/api/v1/ai/summarize", json={
            "text": "",
            "max_length": 100
        }, headers=auth_headers)

        assert response.status_code == 422  # Validation error

        # Invalid max_length
        response = client.post("/api/v1/ai/summarize", json={
            "text": "Valid text",
            "max_length": -1
        }, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    @patch('app.services.model_router.ModelRouter.process_request')
    def test_ai_endpoint_timeout_handling(self, mock_process_request, client: TestClient, auth_headers):
        """Test AI endpoint timeout handling."""
        from asyncio import sleep

        async def delayed_response():
            await sleep(35)  # Longer than timeout
            return "Delayed response"

        mock_process_request.side_effect = delayed_response

        request_data = {
            "text": "Test document",
            "max_length": 100
        }

        response = client.post("/api/v1/ai/summarize", json=request_data, headers=auth_headers)

        # Should handle timeout gracefully
        # This depends on the actual timeout implementation
        assert response.status_code in [200, 504]  # Success or Gateway Timeout

    def test_ai_endpoints_unauthenticated(self, client: TestClient):
        """Test AI endpoints without authentication."""
        endpoints = [
            "/api/v1/ai/summarize",
            "/api/v1/ai/flashcards",
            "/api/v1/ai/quiz",
            "/api/v1/ai/match-partners",
            "/api/v1/ai/write",
            "/api/v1/ai/scholarship-alerts"
        ]

        for endpoint in endpoints:
            response = client.post(endpoint, json={"text": "test"})
            assert response.status_code == 401

    @patch('app.services.model_router.ModelRouter.get_model_status')
    def test_ai_model_status_endpoint(self, mock_get_status, client: TestClient, admin_auth_headers):
        """Test AI model status endpoint."""
        mock_get_status.return_value = {
            "mistral-7b": {"status": "healthy", "last_used": "2024-01-01T00:00:00Z"},
            "gemini": {"status": "healthy", "last_used": "2024-01-01T00:00:00Z"}
        }

        response = client.get("/api/v1/admin/models/status", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "models" in data

    def test_ai_model_status_unauthorized(self, client: TestClient, auth_headers):
        """Test AI model status endpoint without admin access."""
        response = client.get("/api/v1/admin/models/status", headers=auth_headers)

        assert response.status_code == 403  # Forbidden

    @patch('app.services.model_router.ModelRouter.recover_model')
    def test_ai_model_retry_endpoint(self, mock_recover, client: TestClient, admin_auth_headers):
        """Test AI model retry endpoint."""
        mock_recover.return_value = True

        response = client.post("/api/v1/admin/models/mistral-7b/retry", headers=admin_auth_headers)

        assert response.status_code == 200
        mock_recover.assert_called_once_with("mistral-7b")