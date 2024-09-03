import requests

from danswer.db.models import EmbeddingProvider
from danswer.server.manage.embedding.models import TestEmbeddingRequest
from tests.integration.common_utils.constants import API_SERVER_URL
from tests.integration.common_utils.constants import GENERAL_HEADERS
from tests.integration.common_utils.managers.search_settings import (
    SearchSettingsManager,
)
from tests.integration.common_utils.test_models import TestCloudEmbeddingProvider
from tests.integration.common_utils.test_models import TestUser


class EmbeddingProviderManager:
    @staticmethod
    def test(
        user_performing_action: TestUser, embedding_provider: TestCloudEmbeddingProvider
    ) -> None:
        test_embedding_request = TestEmbeddingRequest(
            provider_type=embedding_provider.provider_type,
            api_key=embedding_provider.api_key,
            api_url=embedding_provider.api_url,
        )

        response = requests.post(
            url=f"{API_SERVER_URL}/admin/embedding/test-embedding",
            json=test_embedding_request.model_dump(),
            headers=user_performing_action.headers
            if user_performing_action
            else GENERAL_HEADERS,
        )
        return response.json()

    def create(
        provider_type: EmbeddingProvider,
        api_url: str | None = None,
        api_key: str | None = None,
        user_performing_action: TestUser | None = None,
    ) -> TestCloudEmbeddingProvider:
        embedding_provider_request = {
            "provider_type": provider_type,
            "api_url": api_url,
            "api_key": api_key,
        }

        response = requests.put(
            url=f"{API_SERVER_URL}/admin/embedding/embedding-provider",
            json=embedding_provider_request,
            headers=user_performing_action.headers
            if user_performing_action
            else GENERAL_HEADERS,
        )
        response.raise_for_status()

        response_data = response.json()
        print(response_data)
        return TestCloudEmbeddingProvider(
            provider_type=response_data["provider_type"],
            api_key=response_data.get("api_key"),
            api_url=response_data.get("api_url"),
            model_name=None,
            dimensions=None,
            query_prefix=None,
            passage_prefix=None,
            batch_size=None,
            api_version=None,
        )

    @staticmethod
    def get_all(
        user_performing_action: TestUser | None = None,
    ) -> list[TestCloudEmbeddingProvider]:
        response = requests.get(
            url=f"{API_SERVER_URL}/admin/embedding/embedding-provider",
            headers=user_performing_action.headers
            if user_performing_action
            else GENERAL_HEADERS,
        )

        response.raise_for_status()
        return [
            TestCloudEmbeddingProvider(**embedding_provider)
            for embedding_provider in response.json()
        ]

    @staticmethod
    def edit(
        embedding_provider: TestCloudEmbeddingProvider,
        user_performing_action: TestUser | None = None,
    ) -> None:
        response = requests.put(
            url=f"{API_SERVER_URL}/admin/embedding/embedding-provider",
            json=embedding_provider.model_dump(),
            headers=user_performing_action.headers
            if user_performing_action
            else GENERAL_HEADERS,
        )
        response.raise_for_status()

    @staticmethod
    def delete(
        provider_type: EmbeddingProvider,
        user_performing_action: TestUser | None = None,
    ) -> None:
        response = requests.delete(
            url=f"{API_SERVER_URL}/admin/embedding/embedding-provider/{provider_type}",
            headers=user_performing_action.headers
            if user_performing_action
            else GENERAL_HEADERS,
        )
        response.raise_for_status()

    @staticmethod
    def verify(
        embedding_provider: TestCloudEmbeddingProvider,
        user_performing_action: TestUser | None = None,
    ) -> None:
        current_settings = SearchSettingsManager.get_current(user_performing_action)
        current_provider_type = current_settings.provider_type

        if current_provider_type is None:
            raise ValueError("No current embedding provider found")

        if current_provider_type != embedding_provider.provider_type:
            raise ValueError(
                f"Current embedding provider {current_provider_type} does not match expected {embedding_provider.provider_type}"
            )

        # Additional checks for API key and URL can be added here if needed
        # Note: The actual API key might not be accessible for security reasons
        if current_settings.api_url != embedding_provider.api_url:
            raise ValueError(
                "Current embedding provider API URL does not match expected settings"
            )

    @staticmethod
    def test_embedding(
        provider_type: EmbeddingProvider,
        api_url: str | None = None,
        api_key: str | None = None,
        user_performing_action: TestUser | None = None,
    ) -> None:
        test_request = {
            "provider_type": provider_type,
            "api_url": api_url,
            "api_key": api_key,
        }
        response = requests.post(
            url=f"{API_SERVER_URL}/admin/embedding/test-embedding",
            json=test_request,
            headers=user_performing_action.headers
            if user_performing_action
            else GENERAL_HEADERS,
        )
        response.raise_for_status()
