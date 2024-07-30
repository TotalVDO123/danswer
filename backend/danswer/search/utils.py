from collections.abc import Sequence
from typing import TypeVar

from danswer.chat.models import DocumentRelevance
from danswer.db.models import SearchDoc as DBSearchDoc
from danswer.search.models import InferenceChunk
from danswer.search.models import InferenceSection
from danswer.search.models import SavedSearchDoc
from danswer.search.models import SavedSearchDocWithContent
from danswer.search.models import SearchDoc


T = TypeVar(
    "T",
    InferenceSection,
    InferenceChunk,
    SearchDoc,
    SavedSearchDoc,
    SavedSearchDocWithContent,
)


def dedupe_documents(items: list[T]) -> tuple[list[T], list[int]]:
    seen_ids = set()
    deduped_items = []
    dropped_indices = []
    for index, item in enumerate(items):
        if isinstance(item, InferenceSection):
            document_id = item.center_chunk.document_id
        else:
            document_id = item.document_id

        if document_id not in seen_ids:
            seen_ids.add(document_id)
            deduped_items.append(item)
        else:
            dropped_indices.append(index)
    return deduped_items, dropped_indices


# TODO make more efficient woefull not for now
def relevant_sections_to_indices(
    relevance_chunks: list[DocumentRelevance],
    inference_sections: list[InferenceSection],
) -> list[int]:
    relevant_indices = []
    for index, section in enumerate(inference_sections):
        for relevance_chunk in relevance_chunks:
            if (
                section.center_chunk.document_id == relevance_chunk.document_id
                and section.center_chunk.chunk_id == relevance_chunk.chunk_id
                and relevance_chunk.relevance.relevant
            ):
                relevant_indices.append(index)
                break
    return relevant_indices


def relevant_documents_to_indices(
    relevance_chunks: list[DocumentRelevance], inference_sections: list[DBSearchDoc]
) -> list[int]:
    relevant_indices = []
    for index, section in enumerate(inference_sections):
        for relevance_chunk in relevance_chunks:
            if (
                section.document_id == relevance_chunk.document_id
                and section.chunk_ind == relevance_chunk.chunk_id
                and relevance_chunk.relevance.relevant
            ):
                relevant_indices.append(index)
                break

    return relevant_indices


# danswer/search/utils.py:57: error: "object" has no attribute "document_id"  [attr-defined]
# danswer/search/utils.py:58: error: "object" has no attribute "chunk_ind"  [attr-defined]
# Found 2 errors in 1 file (checked 525 source files)


def drop_llm_indices(
    llm_indices: list[int],
    search_docs: Sequence[DBSearchDoc | SavedSearchDoc],
    dropped_indices: list[int],
) -> list[int]:
    llm_bools = [True if i in llm_indices else False for i in range(len(search_docs))]
    if dropped_indices:
        llm_bools = [
            val for ind, val in enumerate(llm_bools) if ind not in dropped_indices
        ]
    return [i for i, val in enumerate(llm_bools) if val]


def inference_section_from_chunks(
    center_chunk: InferenceChunk,
    chunks: list[InferenceChunk],
) -> InferenceSection | None:
    if not chunks:
        return None

    combined_content = "\n".join([chunk.content for chunk in chunks])

    return InferenceSection(
        center_chunk=center_chunk,
        chunks=chunks,
        combined_content=combined_content,
    )


def chunks_or_sections_to_search_docs(
    items: Sequence[InferenceChunk | InferenceSection] | None,
) -> list[SearchDoc]:
    if not items:
        return []

    search_docs = [
        SearchDoc(
            document_id=(
                chunk := item.center_chunk
                if isinstance(item, InferenceSection)
                else item
            ).document_id,
            chunk_ind=chunk.chunk_id,
            semantic_identifier=chunk.semantic_identifier or "Unknown",
            link=chunk.source_links[0] if chunk.source_links else None,
            blurb=chunk.blurb,
            source_type=chunk.source_type,
            boost=chunk.boost,
            hidden=chunk.hidden,
            metadata=chunk.metadata,
            score=chunk.score,
            match_highlights=chunk.match_highlights,
            updated_at=chunk.updated_at,
            primary_owners=chunk.primary_owners,
            secondary_owners=chunk.secondary_owners,
            is_internet=False,
        )
        for item in items
    ]

    return search_docs
