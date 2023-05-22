from datetime import datetime

from danswer.configs.constants import DocumentSource
from danswer.connectors.models import InputType
from danswer.db.credentials import fetch_credential_by_id
from danswer.db.models import Connector
from danswer.db.models import ConnectorCredentialAssociation
from danswer.server.models import ConnectorSnapshot
from danswer.utils.logging import setup_logger
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

logger = setup_logger()


def fetch_connectors(
    db_session: Session,
    sources: list[DocumentSource] | None = None,
    input_types: list[InputType] | None = None,
    disabled_status: bool | None = None,
) -> list[Connector]:
    stmt = select(Connector)
    if sources:
        stmt = stmt.where(Connector.source.in_(sources))
    if input_types:
        stmt = stmt.where(Connector.input_type.in_(input_types))
    if disabled_status:
        stmt = stmt.where(Connector.disabled.is_(disabled_status))
    results = db_session.scalars(stmt)
    return list(results.all())


def fetch_connector_by_id(connector_id: int, db_session: Session) -> Connector:
    stmt = select(Connector).where(Connector.id == connector_id)
    result = db_session.execute(stmt)
    connector = result.scalar_one()
    return connector


def create_update_connector(
    connector_id: int,
    connector_data: ConnectorSnapshot,
    db_session: Session,
) -> Connector:
    if connector_id != connector_data.id:
        raise ValueError("Conflicting information in trying to update Connector")
    try:
        connector = fetch_connector_by_id(connector_id, db_session)
    except NoResultFound:
        connector = Connector(id=connector_id)
        db_session.add(connector)

    connector.name = connector_data.name
    connector.source = connector_data.source
    connector.input_type = connector_data.input_type
    connector.connector_specific_config = connector_data.connector_specific_config
    connector.refresh_freq = connector_data.refresh_freq
    connector.disabled = connector_data.disabled
    connector.time_updated = datetime.now()

    db_session.commit()
    return connector


def add_credential_to_connector(
    connector_id: int,
    credential_id: int,
    db_session: Session,
) -> Connector:
    connector = fetch_connector_by_id(connector_id, db_session)
    fetch_credential_by_id(credential_id, db_session)  # Just verifies validity
    association = ConnectorCredentialAssociation(
        connector_id=connector_id, credential_id=credential_id
    )
    db_session.add(association)
    db_session.commit()
    return connector
