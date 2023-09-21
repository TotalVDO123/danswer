from sqlalchemy.orm import Session

from danswer.datastores.document_index import get_default_document_index
from danswer.datastores.interfaces import DocumentIndex
from danswer.datastores.interfaces import UpdateRequest
from danswer.db.document import prepare_to_modify_documents
from danswer.db.document_set import fetch_document_sets_for_documents
from danswer.db.document_set import fetch_documents_for_document_set
from danswer.db.document_set import mark_document_set_as_synced
from danswer.db.engine import get_sqlalchemy_engine
from danswer.utils.batching import batch_generator
from danswer.utils.logger import setup_logger

logger = setup_logger()

_SYNC_BATCH_SIZE = 1000


def _sync_document_batch(
    document_ids: list[str], document_index: DocumentIndex
) -> None:
    logger.debug(f"Syncing document sets for: {document_ids}")
    # begin a transaction, release lock at the end
    with Session(get_sqlalchemy_engine(), expire_on_commit=False) as db_session:
        # acquires a lock on the documents so that no other process can modify them
        prepare_to_modify_documents(db_session=db_session, document_ids=document_ids)

        # get current state of document sets for these documents
        document_set_info = fetch_document_sets_for_documents(
            document_ids=document_ids, db_session=db_session
        )

        # update Vespa
        document_index.update(
            update_requests=[
                UpdateRequest(
                    document_ids=[document_id],
                    document_sets=set(document_set_names),
                )
                for document_id, document_set_names in document_set_info
            ]
        )


def sync_document_set(document_set_id: int) -> None:
    document_index = get_default_document_index()
    with Session(get_sqlalchemy_engine()) as db_session:
        documents_to_update = fetch_documents_for_document_set(
            document_set_id=document_set_id, db_session=db_session
        )
        for document_batch in batch_generator(documents_to_update, _SYNC_BATCH_SIZE):
            _sync_document_batch(
                document_ids=[document.id for document in document_batch],
                document_index=document_index,
            )

        mark_document_set_as_synced(
            document_set_id=document_set_id, db_session=db_session
        )
