import os
from typing import Any, Optional

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from .api_key_env import get_api_key_env
from .base_client import BaseLLMClient, normalize_content
from .capabilities import get_capabilities
from .validators import validate_model

# =========================================================
# NORMALIZED CLIENT
# =========================================================

class NormalizedChatOpenAI(ChatOpenAI):

    def __init__(self, **kwargs):

        # IMPORTANT FIX
        kwargs["use_responses_api"] = False

        super().__init__(**kwargs)

    def invoke(self, input, config=None, **kwargs):

        return normalize_content(
            super().invoke(input, config, **kwargs)
        )

    def with_structured_output(
        self,
        schema,
        *,
        method=None,
        **kwargs
    ):

        caps = get_capabilities(self.model_name)

        if caps.preferred_structured_method == "none":
            raise NotImplementedError(
                f"{self.model_name} has no structured output."
            )

        method = method or caps.preferred_structured_method

        if (
            method == "function_calling"
            and not caps.supports_tool_choice
        ):
            kwargs.setdefault("tool_choice", None)

        return super().with_structured_output(
            schema,
            method=method,
            **kwargs
        )

# =========================================================
# HELPERS
# =========================================================

def _input_to_messages(input_: Any) -> list:

    if isinstance(input_, list):
        return input_

    if hasattr(input_, "to_messages"):
        return input_.to_messages()

    return []

# =========================================================
# DEEPSEEK PATCH
# =========================================================

class DeepSeekChatOpenAI(NormalizedChatOpenAI):

    def _get_request_payload(
        self,
        input_,
        *,
        stop=None,
        **kwargs
    ):

        payload = super()._get_request_payload(
            input_,
            stop=stop,
            **kwargs
        )

        outgoing = payload.get("messages", [])

        for message_dict, message in zip(
            outgoing,
            _input_to_messages(input_)
        ):

            if not isinstance(message, AIMessage):
                continue

            reasoning = message.additional_kwargs.get(
                "reasoning_content"
            )

            if reasoning is not None:
                message_dict["reasoning_content"] = reasoning

        return payload

# =========================================================
# CONFIG
# =========================================================

_PASSTHROUGH_KWARGS = (
    "timeout",
    "max_retries",
    "reasoning_effort",
    "temperature",
    "api_key",
    "callbacks",
    "http_client",
    "http_async_client",
)

_PROVIDER_BASE_URL = {
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",
}

# =========================================================
# MAIN CLIENT
# =========================================================

class OpenAIClient(BaseLLMClient):

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        provider: str = "openai",
        **kwargs,
    ):

        super().__init__(
            model,
            base_url,
            **kwargs
        )

        self.provider = provider.lower()

    def get_llm(self):

        self.warn_if_unknown_model()

        llm_kwargs = {
            "model": self.model,

            # FORCE CHAT COMPLETIONS
            "use_responses_api": False,
        }

        if self.base_url:

            llm_kwargs["base_url"] = self.base_url

        api_key = os.environ.get("OPENAI_API_KEY")

        if api_key:
            llm_kwargs["api_key"] = api_key

        for key in _PASSTHROUGH_KWARGS:

            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        return NormalizedChatOpenAI(**llm_kwargs)

    def validate_model(self):

        return validate_model(
            self.provider,
            self.model
        )
