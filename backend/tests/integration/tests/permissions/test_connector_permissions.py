"""
This file takes the happy path to adding a curator to a user group and then tests
the permissions of the curator manipulating connectors.
"""
import pytest
from requests.exceptions import HTTPError

from danswer.server.documents.models import DocumentSource
from tests.integration.common_utils.connector import ConnectorManager
from tests.integration.common_utils.user import TestUser
from tests.integration.common_utils.user import UserManager
from tests.integration.common_utils.user_groups import UserGroupManager


def test_connector_permissions(reset: None) -> None:
    # Creating an admin user (first user created is automatically an admin)
    admin_user: TestUser = UserManager.create(name="admin_user")

    # Creating a curator
    curator: TestUser = UserManager.create(name="curator")

    # Creating a user group
    user_group_1 = UserGroupManager.create(
        name="user_group_1",
        user_ids=[curator.id],
        cc_pair_ids=[],
        user_performing_action=admin_user,
    )
    UserGroupManager.wait_for_user_groups_to_sync(admin_user)
    # setting the user as a curator for the user group
    assert UserGroupManager.set_curator(
        test_user_group=user_group_1,
        user_to_set_as_curator=curator,
        user_performing_action=admin_user,
    )

    # Creating another user group that the user is not a curator of
    user_group_2 = UserGroupManager.create(
        name="user_group_2",
        user_ids=[curator.id],
        cc_pair_ids=[],
        user_performing_action=admin_user,
    )
    UserGroupManager.wait_for_user_groups_to_sync(admin_user)

    # END OF HAPPY PATH

    """
    Curators should not be able to:
    - Create a public connector
    - Create a connector for a user group they are not a curator of
    """
    with pytest.raises(HTTPError):
        ConnectorManager.create(
            name="invalid_connector_1",
            source=DocumentSource.CONFLUENCE,
            groups=[user_group_1.id],
            is_public=True,
            user_performing_action=curator,
        )

    with pytest.raises(HTTPError):
        ConnectorManager.create(
            name="invalid_connector_2",
            source=DocumentSource.CONFLUENCE,
            groups=[user_group_1.id, user_group_2.id],
            is_public=False,
            user_performing_action=curator,
        )

    """
    Curators should be able to:
    - Create a private connector for a user group they are a curator of
    """
    valid_connector = ConnectorManager.create(
        name="valid_connector",
        source=DocumentSource.CONFLUENCE,
        groups=[user_group_1.id],
        is_public=False,
        user_performing_action=curator,
    )
    assert valid_connector.id is not None

    # Verify the created connector
    created_connector = ConnectorManager.get_connector(
        valid_connector.id, user_performing_action=curator
    )
    assert created_connector.name == valid_connector.name
    assert created_connector.source == valid_connector.source

    # Verify that the connector can be found in the list of all connectors
    all_connectors = ConnectorManager.get_all_connectors(user_performing_action=curator)
    assert any(conn.id == valid_connector.id for conn in all_connectors)

    # Test editing the connector
    valid_connector.name = "updated_valid_connector"
    assert ConnectorManager.edit_connector(
        valid_connector, user_performing_action=curator
    )

    # Verify the edit
    updated_connector = ConnectorManager.get_connector(
        valid_connector.id, user_performing_action=curator
    )
    assert updated_connector.name == "updated_valid_connector"

    # Test deleting the connector
    assert ConnectorManager.delete_connector(
        valid_connector, user_performing_action=curator
    )

    # Verify the deletion
    all_connectors_after_delete = ConnectorManager.get_all_connectors(
        user_performing_action=curator
    )
    assert all(conn.id != valid_connector.id for conn in all_connectors_after_delete)

    # Test that curator cannot create a connector for a group they are not a curator of
    with pytest.raises(HTTPError):
        ConnectorManager.create(
            name="invalid_connector_3",
            source=DocumentSource.CONFLUENCE,
            groups=[user_group_2.id],
            is_public=False,
            user_performing_action=curator,
        )

    # Test that curator cannot create a public connector
    with pytest.raises(HTTPError):
        ConnectorManager.create(
            name="invalid_connector_4",
            source=DocumentSource.CONFLUENCE,
            groups=[user_group_1.id],
            is_public=True,
            user_performing_action=curator,
        )
