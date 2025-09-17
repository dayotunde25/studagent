"""
AI Model Router with multi-provider support and circuit breaker logic.
"""
import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.models.system import ModelStatus


class ModelProvider(Enum):
    """Available model providers."""
    OPENROUTER = "openrouter"
    GEMINI = "gemini"
    GROQ = "groq"


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    name: str
    provider: ModelProvider
    model_id: str
    priority: int
    max_tokens: int = 4096
    temperature: float = 0.7


class CircuitBreaker:
    """Circuit breaker for model providers."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 300,  # 5 minutes
        expected_exception: Exception = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False

    def record_success(self):
        """Record a successful execution."""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt a reset."""
        if self.last_failure_time is None:
            return True

        return (datetime.utcnow() - self.last_failure_time) > timedelta(seconds=self.recovery_timeout)


class ModelRouter:
    """Router for AI model calls with fallback and circuit breaker logic."""

    def __init__(self):
        self.models = self._initialize_models()
        self.circuit_breakers = self._initialize_circuit_breakers()
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(settings.LLM_TIMEOUT_SECONDS))

    def _initialize_models(self) -> List[ModelConfig]:
        """Initialize available models."""
        return [
            # OpenRouter models
            ModelConfig(
                name="mistral-7b",
                provider=ModelProvider.OPENROUTER,
                model_id="mistralai/mistral-7b-instruct",
                priority=1,
                max_tokens=8192
            ),
            ModelConfig(
                name="mixtral-8x7b",
                provider=ModelProvider.OPENROUTER,
                model_id="mistralai/mixtral-8x7b-instruct",
                priority=2,
                max_tokens=32768
            ),
            ModelConfig(
                name="llama-3-8b",
                provider=ModelProvider.OPENROUTER,
                model_id="meta-llama/llama-3-8b-instruct",
                priority=3,
                max_tokens=8192
            ),
            ModelConfig(
                name="mistral-instruct",
                provider=ModelProvider.OPENROUTER,
                model_id="mistralai/mistral-7b-instruct",
                priority=4,
                max_tokens=8192
            ),
            ModelConfig(
                name="gemma-7b",
                provider=ModelProvider.OPENROUTER,
                model_id="google/gemma-7b-it",
                priority=5,
                max_tokens=8192
            ),
            # Groq model
            ModelConfig(
                name="groq",
                provider=ModelProvider.GROQ,
                model_id="mixtral-8x7b-32768",
                priority=6,
                max_tokens=32768
            ),
            # Gemini fallback
            ModelConfig(
                name="gemini",
                provider=ModelProvider.GEMINI,
                model_id="gemini-pro",
                priority=7,
                max_tokens=32768
            ),
        ]

    def _initialize_circuit_breakers(self) -> Dict[str, CircuitBreaker]:
        """Initialize circuit breakers for each model."""
        return {
            model.name: CircuitBreaker(
                failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=settings.CIRCUIT_BREAKER_SKIP_MINUTES * 60
            )
            for model in self.models
        }

    async def call_model(
        self,
        prompt: str,
        task_type: str = "general",
        priority_list: Optional[List[str]] = None,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Call an AI model with fallback logic.

        Args:
            prompt: The prompt to send to the model
            task_type: Type of task (summarize, flashcard, quiz, etc.)
            priority_list: Ordered list of model names to try
            **kwargs: Additional parameters for the model

        Returns:
            Tuple of (response_text, model_used)
        """
        if priority_list is None:
            priority_list = [model.name for model in sorted(self.models, key=lambda x: x.priority)]

        for model_name in priority_list:
            model = next((m for m in self.models if m.name == model_name), None)
            if not model:
                continue

            circuit_breaker = self.circuit_breakers[model_name]

            if not circuit_breaker.can_execute():
                continue

            try:
                start_time = time.time()
                response = await self._call_single_model(model, prompt, **kwargs)
                response_time = time.time() - start_time

                # Record success
                circuit_breaker.record_success()

                # Log success
                print(f"Model {model_name} succeeded in {response_time:.2f}s")

                return response, model_name

            except Exception as e:
                # Record failure
                circuit_breaker.record_failure()

                # Log failure
                print(f"Model {model_name} failed: {str(e)}")

                # Continue to next model
                continue

        # All models failed
        raise Exception("All models failed or are unavailable")

    async def _call_single_model(
        self,
        model: ModelConfig,
        prompt: str,
        **kwargs
    ) -> str:
        """Call a single model."""
        if model.provider == ModelProvider.OPENROUTER:
            return await self._call_openrouter(model, prompt, **kwargs)
        elif model.provider == ModelProvider.GEMINI:
            return await self._call_gemini(model, prompt, **kwargs)
        elif model.provider == ModelProvider.GROQ:
            return await self._call_groq(model, prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {model.provider}")

    async def _call_openrouter(
        self,
        model: ModelConfig,
        prompt: str,
        **kwargs
    ) -> str:
        """Call OpenRouter API."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "model": model.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", model.max_tokens),
            "temperature": kwargs.get("temperature", model.temperature),
        }

        response = await self.client.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    async def _call_gemini(
        self,
        model: ModelConfig,
        prompt: str,
        **kwargs
    ) -> str:
        """Call Google Gemini API."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.GEMINI_API_KEY)
            gemini_model = genai.GenerativeModel(model.model_id)

            response = await gemini_model.generate_content_async(prompt)
            return response.text

        except ImportError:
            raise Exception("Google Generative AI library not installed")

    async def _call_groq(
        self,
        model: ModelConfig,
        prompt: str,
        **kwargs
    ) -> str:
        """Call Groq API."""
        try:
            from groq import Groq

            client = Groq(api_key=settings.GROQ_API_KEY)

            response = client.chat.completions.create(
                model=model.model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", model.max_tokens),
                temperature=kwargs.get("temperature", model.temperature),
            )

            return response.choices[0].message.content

        except ImportError:
            raise Exception("Groq library not installed")

    async def get_model_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all models."""
        status = {}
        for model in self.models:
            circuit_breaker = self.circuit_breakers[model.name]
            status[model.name] = {
                "provider": model.provider.value,
                "state": circuit_breaker.state,
                "failure_count": circuit_breaker.failure_count,
                "last_failure": circuit_breaker.last_failure_time.isoformat() if circuit_breaker.last_failure_time else None,
                "can_execute": circuit_breaker.can_execute()
            }
        return status

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global model router instance
model_router = ModelRouter()