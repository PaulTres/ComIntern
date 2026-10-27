"""The deep agent settings that apply to every agent built with the app's model."""

import logging

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    register_harness_profile,
)

from comintern.models.providers import LLMProvider

logger = logging.getLogger(__name__)


def disable_general_purpose_subagent(provider: LLMProvider) -> None:
    """
    Turn off the general-purpose subagent that create_deep_agent adds by default.

    The profile is registered for the model provider, so it applies to every
    deep agent built with that provider's model, not only to one agent. It must
    be registered before any agent is built.

    :param provider: The provider of the app's chat model
    """
    register_harness_profile(
        provider.value,
        HarnessProfile(
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ),
    )
    logger.info("Disabled the general-purpose subagent for provider=%s", provider.value)
