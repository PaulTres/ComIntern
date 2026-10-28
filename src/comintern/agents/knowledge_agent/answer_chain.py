from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from comintern.agents.audience import AUDIENCE_INSTRUCTIONS
from comintern.agents.knowledge_agent.helpers import build_passages
from comintern.agents.knowledge_agent.prompts import (
    ANSWER_INPUT_TEMPLATE,
    ANSWER_SYSTEM_PROMPT,
    NO_HISTORY_TEXT,
    NO_PASSAGES_TEXT,
)
from comintern.models.chat import Audience
from comintern.models.knowledge import Chunk, ConversationTurn

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [("system", ANSWER_SYSTEM_PROMPT), ("human", ANSWER_INPUT_TEMPLATE)]
)


def build_answer_chain(chat_model: BaseChatModel) -> Runnable[dict[str, str], str]:
    """
    :return: The prompt, then the model, streaming the answer piece by piece.
    """
    return (ANSWER_PROMPT | chat_model | StrOutputParser()).with_config(
        run_name="knowledge_answer"
    )


def build_answer_input(
    question: str,
    history: list[ConversationTurn],
    chunks: list[Chunk],
    audience: Audience | None,
) -> dict[str, str]:
    """
    :return: The prompt's placeholders: the conversation, the question, the passages and the tone.
    """
    return {
        "history": "\n".join(
            f"User: {turn.question}\nAssistant: {turn.answer}" for turn in history
        )
        or NO_HISTORY_TEXT,
        "question": question,
        "passages": "\n\n".join(
            f"({title})\n{text}" for title, text in build_passages(chunks)
        )
        or NO_PASSAGES_TEXT,
        "audience": AUDIENCE_INSTRUCTIONS[audience],
    }
