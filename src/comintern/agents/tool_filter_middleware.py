"""The middleware that offers a deep agent only its own tools, and runs only those."""

import logging
from collections.abc import Awaitable, Callable, Collection
from typing import Any

from langchain.agents.middleware import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
    ToolCallRequest,
)
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from langgraph.types import Command

logger = logging.getLogger(__name__)

REFUSED_TOOL_CALL_TEXT = "Error: {tool_name} is not one of your tools. Use only yours."


def get_tool_name(tool: BaseTool | dict[str, Any]) -> str:
    """
    Get the name of a tool, which a request may hold as a tool or as a dict

    :param tool: The tool, or its dict description
    :return: The tool name
    """
    return tool.get("name", "") if isinstance(tool, dict) else tool.name


class ToolFilterMiddleware(AgentMiddleware):
    """
    Offer the model only the tools on an allow-list, and refuse a call to any other.

    deepagents adds file tools and a to-do tool to every agent. An agent that must
    not use them is built with this middleware and the names of its own tools, so
    the model is never offered them. They stay registered in the graph, so a call
    the model makes to one by name is answered with an error instead of running.
    """

    def __init__(self, allowed_tool_names: Collection[str]) -> None:
        """
        Fix the allow-list the middleware keeps the tools to

        :param allowed_tool_names: The names of the tools the model may be offered
        """
        super().__init__()
        self._allowed_tool_names = frozenset(allowed_tool_names)

    def _filter_tools(self, request: ModelRequest) -> ModelRequest:
        """
        Keep only the tools on the allow-list

        :param request: The model request
        :return: The same request without the tools deepagents adds
        """
        return request.override(
            tools=[
                tool
                for tool in request.tools
                if get_tool_name(tool) in self._allowed_tool_names
            ]
        )

    def _build_refused_tool_call_message(
        self, request: ToolCallRequest
    ) -> ToolMessage | None:
        """
        Build the error the model reads for a call to a tool off the allow-list

        :param request: The tool call request
        :return: The error message; None when the tool is on the allow-list and runs
        """
        tool_name = request.tool_call["name"]
        if tool_name in self._allowed_tool_names:
            return None

        logger.warning("Refused a call to tool=%s, which is not allowed", tool_name)
        return ToolMessage(
            content=REFUSED_TOOL_CALL_TEXT.format(tool_name=tool_name),
            name=tool_name,
            tool_call_id=request.tool_call["id"],
            status="error",
        )

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """
        Filter the tools, then call the model

        :param request: The model request
        :param handler: Calls the model
        :return: The model response
        """
        return await handler(self._filter_tools(request))

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        The same as awrap_model_call, when the agent runs synchronously

        :param request: The model request
        :param handler: Calls the model
        :return: The model response
        """
        return handler(self._filter_tools(request))

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """
        Refuse a call to a tool off the allow-list, or run the tool

        :param request: The tool call request
        :param handler: Runs the tool
        :return: The error for a refused call, or what the tool returns
        """
        return self._build_refused_tool_call_message(request) or await handler(request)

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """
        The same as awrap_tool_call, when the agent runs synchronously

        :param request: The tool call request
        :param handler: Runs the tool
        :return: The error for a refused call, or what the tool returns
        """
        return self._build_refused_tool_call_message(request) or handler(request)
