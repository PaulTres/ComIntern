"""Combine, join and cite the passages the retrieval agent found."""

from comintern.models.chat import SourceResponseModel
from comintern.models.knowledge import Chunk


def merge_chunks(
    saved_chunks: list[Chunk] | None, new_chunks: list[Chunk] | None
) -> list[Chunk]:
    """
    Combine the saved chunks with the ones a tool just added, each chunk once, keeping its best score.

    :return: Both lists combined.
    """
    chunks = sorted(
        [*(saved_chunks or []), *(new_chunks or [])], key=lambda chunk: chunk.score
    )
    return list(
        {(chunk.source_id, chunk.chunk_index): chunk for chunk in chunks}.values()
    )


def build_sources(chunks: list[Chunk]) -> list[SourceResponseModel]:
    """
    :return: One source per document among the chunks, with its best score, best first.
    """
    best: dict[str, SourceResponseModel] = {}
    for chunk in chunks:
        current = best.get(chunk.source_id)
        if current is None or chunk.score > current.score:
            best[chunk.source_id] = SourceResponseModel(
                title=chunk.title, score=round(chunk.score, 3)
            )
    return sorted(best.values(), key=lambda source: source.score, reverse=True)


def build_passages(chunks: list[Chunk]) -> list[tuple[str, str]]:
    """
    Join chunks that follow each other in the same source into one passage, without the text
    the splitter repeats between them.

    :return: (title, text) per passage, the most relevant first.
    """
    runs: list[list[Chunk]] = []
    for chunk in sorted(chunks, key=lambda chunk: (chunk.source_id, chunk.chunk_index)):
        previous = runs[-1][-1] if runs else None
        if (
            previous
            and chunk.source_id == previous.source_id
            and chunk.chunk_index == previous.chunk_index + 1
        ):
            runs[-1].append(chunk)
        else:
            runs.append([chunk])
    runs.sort(key=lambda run: max(chunk.score for chunk in run), reverse=True)
    return [(run[0].title, _join_run(run)) for run in runs]


def _join_run(run: list[Chunk]) -> str:
    text = run[0].text
    for chunk in run[1:]:
        # Each passage repeats its title on the first line (KnowledgeBase.index); the run has it once.
        body = chunk.text.removeprefix(f"{chunk.title}\n")
        overlap = _overlap_length(text, body)
        text += body[overlap:] if overlap else "\n" + body
    return text


def _overlap_length(text: str, following: str) -> int:
    """
    :return: How many characters at the start of `following` the end of `text` already has.
    """
    for length in range(min(len(text), len(following)), 0, -1):
        if text.endswith(following[:length]):
            return length
    return 0
