from io import IO
from typing import List

import requests

from danswer.file_store.models import FileDescriptor
from tests.integration.common_utils.constants import API_SERVER_URL
from tests.integration.common_utils.constants import GENERAL_HEADERS
from tests.integration.common_utils.test_models import DATestUser


class FileManager:
    @staticmethod
    def upload_files(
        files: List[tuple[str, IO]],
        user_performing_action: DATestUser | None = None,
    ) -> List[FileDescriptor]:
        headers = (
            user_performing_action.headers
            if user_performing_action
            else GENERAL_HEADERS
        )

        files_param = []
        for filename, file_obj in files:
            files_param.append(
                ("files", (filename, file_obj, "application/octet-stream"))
            )

        response = requests.post(
            f"{API_SERVER_URL}/chat/file",
            files=files_param,
            headers=headers,
        )

        if not response.ok:
            print(response.json())

            return (
                [],
                f"Failed to upload files - {response.json().get('detail', 'Unknown error')}",
            )

        response_json = response.json()
        print(response_json)
        return response_json.get("files", []), None

    @staticmethod
    def fetch_chat_file(
        file_id: str,
        user_performing_action: DATestUser | None = None,
    ) -> bytes:
        response = requests.get(
            f"{API_SERVER_URL}/file/{file_id}",
            headers=user_performing_action.headers
            if user_performing_action
            else GENERAL_HEADERS,
        )
        response.raise_for_status()
        return response.content

    @staticmethod
    def fetch_query_file(
        file_id: str,
        user_performing_action: DATestUser | None = None,
    ) -> None:
        requests.get(
            f"{API_SERVER_URL}/query/file/{file_id}",
            headers=user_performing_action.headers
            if user_performing_action
            else GENERAL_HEADERS,
        )
