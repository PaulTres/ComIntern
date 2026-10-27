"""Build the configured chat model."""

import logging

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from comintern.configuration.config import LLMSettings
from comintern.exceptions import AppError, AppErrorCode
from comintern.models.providers import LLMProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """Builds the chat model the settings name."""

    @staticmethod
    def create_chat_model(llm_settings: LLMSettings) -> BaseChatModel:
        """
        :param llm_settings: The provider, model and limits.
        :return: The chat model.
        """
        match llm_settings.provider:
            case LLMProvider.OLLAMA:
                logger.info(
                    "Creating Ollama model %s at %s",
                    llm_settings.model_name,
                    llm_settings.base_url,
                )
                return ChatOllama(
                    model=llm_settings.model_name,
                    base_url=llm_settings.base_url,
                    temperature=llm_settings.temperature,
                    num_predict=llm_settings.max_tokens,
                    reasoning=llm_settings.reasoning,
                    client_kwargs={
                        "timeout": httpx.Timeout(timeout=llm_settings.timeout_seconds)
                    },
                )
            case _:
                logger.error("Unsupported LLM provider=%s", llm_settings.provider)
                raise AppError(AppErrorCode.INTERNAL_SERVER_ERROR)
