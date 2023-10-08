import base64
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import requests

from danswer.configs.app_configs import CONTINUE_ON_CONNECTOR_FAILURE
from danswer.configs.app_configs import INDEX_BATCH_SIZE
from danswer.configs.constants import DocumentSource
from danswer.connectors.interfaces import GenerateDocumentsOutput
from danswer.connectors.interfaces import LoadConnector
from danswer.connectors.interfaces import PollConnector
from danswer.connectors.interfaces import SecondsSinceUnixEpoch
from danswer.connectors.models import ConnectorMissingCredentialError
from danswer.connectors.models import Document
from danswer.connectors.models import Section
from danswer.utils.logger import setup_logger


logger = setup_logger()

GONG_BASE_URL = "https://us-34014.api.gong.io"


class GongConnector(LoadConnector, PollConnector):
    def __init__(
        self,
        workspaces: list[str] | None = None,
        batch_size: int = INDEX_BATCH_SIZE,
        use_end_time: bool = False,
        continue_on_fail: bool = CONTINUE_ON_CONNECTOR_FAILURE,
        hide_user_info: bool = False,
    ) -> None:
        self.workspaces = workspaces
        self.batch_size: int = batch_size
        self.continue_on_fail = continue_on_fail
        self.auth_token_basic: str | None = None
        self.use_end_time = use_end_time
        self.hide_user_info = hide_user_info

    def _get_auth_header(self) -> dict[str, str]:
        if self.auth_token_basic is None:
            raise ConnectorMissingCredentialError("Gong")

        return {"Authorization": f"Basic {self.auth_token_basic}"}

    def _get_workspace_id_map(self) -> dict[str, str]:
        url = f"{GONG_BASE_URL}/v2/workspaces"
        response = requests.get(url, headers=self._get_auth_header())
        response.raise_for_status()

        workspaces_details = response.json().get("workspaces")
        return {workspace["name"]: workspace["id"] for workspace in workspaces_details}

    def _get_transcript_batches(
        self, start_datetime: str = None, end_datetime: str = None
    ) -> list[str]:
        url = f"{GONG_BASE_URL}/v2/calls/transcript"
        body = {"filter": {}}
        if start_datetime:
            body["filter"]["fromDateTime"] = start_datetime
        if end_datetime:
            body["filter"]["toDateTime"] = end_datetime

        # The batch_ids in the previous method appears to be batches of call_ids to process
        # In this method, we will retrieve transcripts for them in batches.
        transcripts = []
        workspace_list = self.workspaces or [None]
        workspace_map = self._get_workspace_id_map() if self.workspaces else {}

        for workspace in workspace_list:
            if workspace:
                logger.info(f"Updating workspace: {workspace}")
                workspace_id = workspace_map.get(workspace)
                if not workspace_id:
                    logger.error(f"Invalid workspace: {workspace}")
                    if not self.continue_on_fail:
                        raise ValueError(f"Invalid workspace: {workspace}")
                    continue
                body["filter"]["workspaceId"] = workspace_id
            else:
                if "workspaceId" in body["filter"]:
                    del body["filter"]["workspaceId"]

            while True:
                response = requests.post(
                    url, headers=self._get_auth_header(), json=body
                )
                response.raise_for_status()

                data = response.json()
                call_transcripts = data.get("callTranscripts", [])
                transcripts.extend(call_transcripts)

                while len(transcripts) >= self.batch_size:
                    yield transcripts[: self.batch_size]
                    transcripts = transcripts[self.batch_size :]

                cursor = data.get("records", {}).get("cursor")
                if cursor:
                    body["cursor"] = cursor
                else:
                    break

        if transcripts:
            yield transcripts

    def _get_call_details_by_ids(self, call_ids: list[str]) -> dict:
        url = f"{GONG_BASE_URL}/v2/calls/extensive"

        body = {
            "filter": {"callIds": call_ids},
            "contentSelector": {"exposedFields": {"parties": True}},
        }

        response = requests.post(url, headers=self._get_auth_header(), json=body)
        response.raise_for_status()

        calls = response.json().get("calls")
        call_to_metadata = {}
        for call in calls:
            call_to_metadata[call["metaData"]["id"]] = call

        return call_to_metadata

    @staticmethod
    def _parse_parties(parties: list[dict]) -> dict[str, str]:
        id_mapping = {}
        for party in parties:
            name = party.get("name")
            email = party.get("emailAddress")

            if name and email:
                full_identifier = f"{name} ({email})"
            elif name:
                full_identifier = name
            elif email:
                full_identifier = email
            else:
                full_identifier = "Unknown"

            id_mapping[party["speakerId"]] = full_identifier

        return id_mapping

    def _fetch_calls(
        self, start_datetime: str = None, end_datetime: str = None
    ) -> GenerateDocumentsOutput:
        for transcript_batch in self._get_transcript_batches(
            start_datetime, end_datetime
        ):
            doc_batch: list[Document] = []

            call_ids = [t.get("callId") for t in transcript_batch if t.get("callId")]
            call_details_map = self._get_call_details_by_ids(call_ids)

            for transcript in transcript_batch:
                call_id = transcript.get("callId")

                if not call_id or call_id not in call_details_map:
                    logger.error(
                        f"Couldn't get call information for Call ID: {call_id}"
                    )
                    if not self.continue_on_fail:
                        raise RuntimeError(
                            f"Couldn't get call information for Call ID: {call_id}"
                        )
                    continue

                call_details = call_details_map[call_id]

                call_metadata = call_details["metaData"]
                call_parties = call_details["parties"]

                id_to_name_map = self._parse_parties(call_parties)

                contents = transcript.get("transcript")

                # Keeping a separate dict here in case the parties info is incomplete
                speaker_to_name: dict[str, str] = {}

                transcript_text = ""
                call_title = call_metadata["title"]
                if call_title:
                    transcript_text += f"Call Title: {call_title}\n\n"

                call_purpose = call_metadata["purpose"]
                if call_purpose:
                    transcript_text += f"Call Description: {call_purpose}\n\n"

                for segment in contents:
                    speaker_id = segment.get("speakerId", "")
                    if speaker_id not in speaker_to_name:
                        if self.hide_user_info:
                            speaker_to_name[
                                speaker_id
                            ] = f"User {len(speaker_to_name) + 1}"
                        else:
                            speaker_to_name[speaker_id] = id_to_name_map.get(
                                speaker_id, "Unknown"
                            )

                    speaker_name = speaker_to_name[speaker_id]

                    sentences = segment.get("sentences", {})
                    monolog = " ".join(
                        [sentence.get("text", "") for sentence in sentences]
                    )
                    transcript_text += f"{speaker_name}: {monolog}\n\n"

                doc_batch.append(
                    Document(
                        id=call_id,
                        sections=[
                            Section(link=call_metadata["url"], text=transcript_text)
                        ],
                        source=DocumentSource.GONG,
                        # Should not ever be Untitled as a call cannot be made without a Title
                        semantic_identifier=call_title or "Untitled",
                        metadata={"Start Time": call_metadata["started"]},
                    )
                )
            yield doc_batch

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        combined = (
            f'{credentials["gong_access_key"]}:{credentials["gong_access_key_secret"]}'
        )
        self.auth_token_basic = base64.b64encode(combined.encode("utf-8")).decode(
            "utf-8"
        )
        return None

    def load_from_state(self) -> GenerateDocumentsOutput:
        return self._fetch_calls()

    def poll_source(
        self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch
    ) -> GenerateDocumentsOutput:
        # Because these are meeting start times, the meeting needs to end and be processed
        # so adding a 1 day buffer and fetching by default till current time
        start_datetime = datetime.fromtimestamp(start, tz=timezone.utc)
        start_one_day_offset = start_datetime - timedelta(days=1)
        start_time = start_one_day_offset.isoformat()
        end_time = (
            datetime.fromtimestamp(end, tz=timezone.utc).isoformat()
            if self.use_end_time
            else None
        )

        return self._fetch_calls(start_time, end_time)


if __name__ == "__main__":
    import os
    import time

    connector = GongConnector()
    connector.load_credentials(
        {
            "gong_access_key": os.environ["GONG_ACCESS_KEY"],
            "gong_access_key_secret": os.environ["GONG_ACCESS_KEY_SECRET"],
        }
    )

    current = time.time()
    one_day_ago = current - 24 * 60 * 60  # 1 day
    latest_docs = connector.poll_source(one_day_ago, current)
    print(next(latest_docs))
