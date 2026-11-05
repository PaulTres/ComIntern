"""The events a chat turn is streamed as (server-sent events), one model per event."""

from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel

from comintern.models.chat import SourceResponseModel


class StreamEventType(StrEnum):
    """Sent as the event's `event:` line."""

    PROGRESS = "progress"
    DELTA = "delta"
    PAYLOAD = "payload"
    ERROR = "error"
    FINAL = "final"


class PayloadType(StrEnum):
    """What a payload event carries."""

    SOURCES = "sources"


class ProgressStep(StrEnum):
    """Shown to the user as they are while a turn runs, so each is a sentence."""

    CLASSIFYING = "Working out who should answer"
    SEARCHING = "Searching the regulations and your documents"
    READING_STATUS = "Reading your compliance status"
    WRITING = "Writing the answer"


class StreamEventModel(BaseModel):
    """One event of a chat stream; each subclass names the event it is sent as."""

    event_type: ClassVar[StreamEventType]


class ProgressEventModel(StreamEventModel):
    """What the assistant is doing; not part of the stored answer."""

    event_type = StreamEventType.PROGRESS
    step: str


class DeltaEventModel(StreamEventModel):
    """The next piece of the answer; joined in order they are the stored answer."""

    event_type = StreamEventType.DELTA
    text: str


class PayloadEventModel(StreamEventModel):
    """The documents the answer was written from; at most one per turn."""

    event_type = StreamEventType.PAYLOAD
    type: PayloadType = PayloadType.SOURCES
    value: list[SourceResponseModel]


class ErrorEventModel(StreamEventModel):
    """A failure after the stream started; it ends the stream."""

    event_type = StreamEventType.ERROR
    code: str
    detail: str


class FinalEventModel(StreamEventModel):
    """The answer is saved; it ends the stream."""

    event_type = StreamEventType.FINAL
    conversation_id: int
    message_id: int
