import io
import os
from collections.abc import Callable
from collections.abc import Collection
from datetime import datetime
from datetime import timezone
from functools import lru_cache
from typing import Any
from typing import cast
from urllib.parse import urlparse

import bs4
from atlassian import Confluence  # type:ignore
from requests import HTTPError

from danswer.configs.app_configs import CONFLUENCE_CONNECTOR_INDEX_ONLY_ACTIVE_PAGES
from danswer.configs.app_configs import CONFLUENCE_CONNECTOR_LABELS_TO_SKIP
from danswer.configs.app_configs import CONFLUENCE_CONNECTOR_SKIP_LABEL_INDEXING
from danswer.configs.app_configs import CONTINUE_ON_CONNECTOR_FAILURE
from danswer.configs.app_configs import INDEX_BATCH_SIZE
from danswer.configs.constants import DocumentSource
from danswer.connectors.confluence.rate_limit_handler import (
    make_confluence_call_handle_rate_limit,
)
from danswer.connectors.cross_connector_utils.html_utils import format_document_soup
from danswer.connectors.interfaces import GenerateDocumentsOutput
from danswer.connectors.interfaces import LoadConnector
from danswer.connectors.interfaces import PollConnector
from danswer.connectors.interfaces import SecondsSinceUnixEpoch
from danswer.connectors.models import BasicExpertInfo
from danswer.connectors.models import ConnectorMissingCredentialError
from danswer.connectors.models import Document
from danswer.connectors.models import Section
from danswer.file_processing.extract_file_text import extract_file_text
from danswer.file_processing.html_utils import format_document_soup
from danswer.utils.logger import setup_logger

logger = setup_logger()

# Potential Improvements
# 1. If wiki page instead of space, do a search of all the children of the page instead of index all in the space: DONE
# 2. Include attachments, etc
# 3. Segment into Sections for more accurate linking, can split by headers but make sure no text/ordering is lost


def _extract_confluence_keys_from_cloud_url(wiki_url: str) -> tuple[str, str, str]:
    """Sample
    https://danswer.atlassian.net/wiki/spaces/1234abcd/pages/5678efgh/overview
    https://danswer.atlassian.net/wiki/spaces/ASAM/overview
    wiki_base is https://danswer.atlassian.net/wiki
    space is 1234abcd
    page_id is 5678efgh
    """
    parsed_url = urlparse(wiki_url)
    wiki_base = (
        parsed_url.scheme
        + "://"
        + parsed_url.netloc
        + parsed_url.path.split("/spaces")[0]
    )
    path_parts = parsed_url.path.split("/")
    space = path_parts[3]
    page_id = path_parts[5] if len(path_parts) > 5 else ""
    return wiki_base, space, page_id


def _extract_confluence_keys_from_datacenter_url(wiki_url: str) -> tuple[str, str, str]:
    """Sample
    https://danswer.ai/confluence/display/1234abcd/pages/5678efgh/overview
    wiki_base is https://danswer.ai/confluence
    space is 1234abcd
    page_id is 5678efgh
    """
    # /display/ is always right before the space and at the end of the base url
    DISPLAY = "/display/"

    parsed_url = urlparse(wiki_url)
    wiki_base = (
        parsed_url.scheme
        + "://"
        + parsed_url.netloc
        + parsed_url.path.split(DISPLAY)[0]
    )
    space = DISPLAY.join(parsed_url.path.split(DISPLAY)[1:]).split("/")[0]
    page_id = parsed_url.path.split("/")[5]
    return wiki_base, space, page_id


def extract_confluence_keys_from_url(wiki_url: str) -> tuple[str, str, str, bool]:
    is_confluence_cloud = (
        ".atlassian.net/wiki/spaces/" in wiki_url
        or ".jira.com/wiki/spaces/" in wiki_url
    )

    try:
        if is_confluence_cloud:
            wiki_base, space, page_id = _extract_confluence_keys_from_cloud_url(wiki_url)
        else:
            wiki_base, space, page_id = _extract_confluence_keys_from_datacenter_url(wiki_url)
    except Exception as e:
        error_msg = f"Not a valid Confluence Wiki Link, unable to extract wiki base, space, and page id. Exception: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    print(f"wiki_base: {wiki_base}, space: {space}, page_id: {page_id}, is_confluence_cloud: {is_confluence_cloud}")

    return wiki_base, space, page_id, is_confluence_cloud


@lru_cache()
def _get_user(user_id: str, confluence_client: Confluence) -> str:
    """Get Confluence Display Name based on the account-id or userkey value

    Args:
        user_id (str): The user id (i.e: the account-id or userkey)
        confluence_client (Confluence): The Confluence Client

    Returns:
        str: The User Display Name. 'Unknown User' if the user is deactivated or not found
    """
    user_not_found = "Unknown User"

    get_user_details_by_accountid = make_confluence_call_handle_rate_limit(
        confluence_client.get_user_details_by_accountid
    )
    try:
        return get_user_details_by_accountid(user_id).get("displayName", user_not_found)
    except Exception as e:
        logger.warning(
            f"Unable to get the User Display Name with the id: '{user_id}' - {e}"
        )
    return user_not_found


def parse_html_page(text: str, confluence_client: Confluence) -> str:
    """Parse a Confluence html page and replace the 'user Id' by the real
        User Display Name

    Args:
        text (str): The page content
        confluence_client (Confluence): Confluence client

    Returns:
        str: loaded and formated Confluence page
    """
    soup = bs4.BeautifulSoup(text, "html.parser")
    for user in soup.findAll("ri:user"):
        user_id = (
            user.attrs["ri:account-id"]
            if "ri:account-id" in user.attrs
            else user.get("ri:userkey")
        )
        if not user_id:
            logger.warning(
                "ri:userkey not found in ri:user element. " f"Found attrs: {user.attrs}"
            )
            continue
        # Include @ sign for tagging, more clear for LLM
        user.replaceWith("@" + _get_user(user_id, confluence_client))
    return format_document_soup(soup)


def get_used_attachments(text: str, confluence_client: Confluence) -> list[str]:
    """Parse a Confluence html page to generate a list of current
        attachment in used

    Args:
        text (str): The page content
        confluence_client (Confluence): Confluence client

    Returns:
        list[str]: List of filename currently in used
    """
    files_in_used = []
    soup = bs4.BeautifulSoup(text, "html.parser")
    for attachment in soup.findAll("ri:attachment"):
        files_in_used.append(attachment.attrs["ri:filename"])
    return files_in_used


def _comment_dfs(
    comments_str: str,
    comment_pages: Collection[dict[str, Any]],
    confluence_client: Confluence,
) -> str:
    get_page_child_by_type = make_confluence_call_handle_rate_limit(
        confluence_client.get_page_child_by_type
    )

    for comment_page in comment_pages:
        comment_html = comment_page["body"]["storage"]["value"]
        comments_str += "\nComment:\n" + parse_html_page(
            comment_html, confluence_client
        )
        child_comment_pages = get_page_child_by_type(
            comment_page["id"],
            type="comment",
            start=None,
            limit=None,
            expand="body.storage.value",
        )
        comments_str = _comment_dfs(
            comments_str, child_comment_pages, confluence_client
        )
    return comments_str


class ConfluenceConnector(LoadConnector, PollConnector):
    def __init__(
        self,
        wiki_page_url: str,
        batch_size: int = INDEX_BATCH_SIZE,
        continue_on_failure: bool = CONTINUE_ON_CONNECTOR_FAILURE,
        # if a page has one of the labels specified in this list, we will just
        # skip it. This is generally used to avoid indexing extra sensitive
        # pages.
        labels_to_skip: list[str] = CONFLUENCE_CONNECTOR_LABELS_TO_SKIP,
    ) -> None:
        self.batch_size = batch_size
        self.continue_on_failure = continue_on_failure
        self.labels_to_skip = set(labels_to_skip)
        self.wiki_base, self.space, self.page_id, self.is_cloud = extract_confluence_keys_from_url(
            wiki_page_url
        )
        self.space_level_scan = False
        if self.page_id is None or self.page_id == "":
            self.space_level_scan = True
        self.confluence_client: Confluence | None = None

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        username = credentials["confluence_username"]
        access_token = credentials["confluence_access_token"]
        self.confluence_client = Confluence(
            url=self.wiki_base,
            # passing in username causes issues for Confluence data center
            username=username if self.is_cloud else None,
            password=access_token if self.is_cloud else None,
            token=access_token if not self.is_cloud else None,
            cloud=self.is_cloud,
        )
        return None

    def _fetch_pages(
        self,
        confluence_client: Confluence,
        start_ind: int,
    ) -> Collection[dict[str, Any]]:
        def _fetch_space(start_ind: int, batch_size: int) -> Collection[dict[str, Any]]:
            get_all_pages_from_space = make_confluence_call_handle_rate_limit(
                confluence_client.get_all_pages_from_space
            )
            try:
                return get_all_pages_from_space(
                    self.space,
                    start=start_ind,
                    limit=batch_size,
                    status="current"
                    if CONFLUENCE_CONNECTOR_INDEX_ONLY_ACTIVE_PAGES
                    else None,
                    expand="body.storage.value,version",
                )
            except Exception:
                logger.warning(
                    f"Batch failed with space {self.space} at offset {start_ind} "
                    f"with size {batch_size}, processing pages individually..."
                )

                view_pages: list[dict[str, Any]] = []
                for i in range(self.batch_size):
                    try:
                        # Could be that one of the pages here failed due to this bug:
                        # https://jira.atlassian.com/browse/CONFCLOUD-76433
                        view_pages.extend(
                            get_all_pages_from_space(
                                self.space,
                                start=start_ind + i,
                                limit=1,
                                status="current"
                                if CONFLUENCE_CONNECTOR_INDEX_ONLY_ACTIVE_PAGES
                                else None,
                                expand="body.storage.value,version",
                            )
                        )
                    except HTTPError as e:
                        logger.warning(
                            f"Page failed with space {self.space} at offset {start_ind + i}, "
                            f"trying alternative expand option: {e}"
                        )
                        # Use view instead, which captures most info but is less complete
                        view_pages.extend(
                            get_all_pages_from_space(
                                self.space,
                                start=start_ind + i,
                                limit=1,
                                expand="body.view.value,version",
                            )
                        )

                return view_pages

        def _fetch_child_pages(start_ind: int, batch_size: int) -> Collection[dict[str, Any]]:
            get_page_child_by_type = make_confluence_call_handle_rate_limit(
                confluence_client.get_page_child_by_type
            )
            try:
                return get_page_child_by_type(
                    self.page_id,
                    type="page",
                    start=start_ind,
                    limit=batch_size,
                    expand="body.storage.value,version",
                )
            except Exception:
                logger.warning(
                    f"Batch failed with page {self.page_id} at offset {start_ind} "
                    f"with size {batch_size}, processing pages individually..."
                )

                child_pages: list[dict[str, Any]] = []
                for i in range(self.batch_size):
                    ind = start_ind + i
                    try:
                        child_page = get_page_child_by_type(
                            self.page_id,
                            type="page",
                            start=ind,
                            limit=1,
                            expand="body.storage.value,version",
                        )
                        child_pages.extend(child_page)
                    except Exception as e:
                        logger.warning(
                            f"Page {self.page_id} at offset {ind} failed: {e}"
                        )
                        if not self.continue_on_failure:
                            raise e

                return child_pages

        pages: list[dict[str, Any]] = []
        # batch = _fetch(start_ind, self.batch_size)
        batch = (
            _fetch_space(start_ind, self.batch_size)
            if self.space_level_scan
            else _fetch_child_pages(start_ind, self.batch_size)
        )
        pages.extend(batch)
        while batch:
            start_ind += self.batch_size
            batch = (
                _fetch_space(start_ind, self.batch_size)
                if self.space_level_scan
                else _fetch_child_pages(start_ind, self.batch_size)
            )
            pages.extend(batch)
        return pages

    def _fetch_comments(self, confluence_client: Confluence, page_id: str) -> str:
        get_page_child_by_type = make_confluence_call_handle_rate_limit(
            confluence_client.get_page_child_by_type
        )
        try:
            comment_pages = cast(
                Collection[dict[str, Any]],
                get_page_child_by_type(
                    page_id,
                    type="comment",
                    start=None,
                    limit=None,
                    expand="body.storage.value",
                ),
            )
            return _comment_dfs("", comment_pages, confluence_client)
        except Exception as e:
            if not self.continue_on_failure:
                raise e

            logger.exception(
                "Ran into exception when fetching comments from Confluence"
            )
            return ""

    def _fetch_labels(self, confluence_client: Confluence, page_id: str) -> list[str]:
        get_page_labels = make_confluence_call_handle_rate_limit(
            confluence_client.get_page_labels
        )
        try:
            labels_response = get_page_labels(page_id)
            return [label["name"] for label in labels_response["results"]]
        except Exception as e:
            if not self.continue_on_failure:
                raise e

            logger.exception("Ran into exception when fetching labels from Confluence")
            return []

    def _fetch_attachments(
        self, confluence_client: Confluence, page_id: str, files_in_used: list[str]
    ) -> str:
        get_attachments_from_content = make_confluence_call_handle_rate_limit(
            confluence_client.get_attachments_from_content
        )
        files_attachment_content: list = []

        try:
            attachments_container = get_attachments_from_content(
                page_id, start=0, limit=500
            )
            for attachment in attachments_container["results"]:
                if attachment["metadata"]["mediaType"] in ["image/jpeg", "image/png", "image/gif", "image/svg+xml", "video/mp4", "video/quicktime"]:
                    continue

                if attachment["title"] not in files_in_used:
                    continue

                download_link = confluence_client.url + attachment["_links"]["download"]
                response = confluence_client._session.get(download_link)

                if response.status_code == 200:
                    extract = extract_file_text(
                        file_name = attachment["title"],
                        file = io.BytesIO(response.content),
                        break_on_unprocessable = False
                    )
                    files_attachment_content.append(extract)

        except Exception as e:
            if not self.continue_on_failure:
                raise e
            logger.exception(
                f"Ran into exception when fetching attachments from Confluence: {e}"
            )

        return "\n".join(files_attachment_content)

    def _get_doc_batch(
            self, start_ind: int, time_filter: Callable[[datetime], bool] | None = None
    ) -> tuple[list[Document], int]:
        doc_batch: list[Document] = []

        if self.confluence_client is None:
            raise ConnectorMissingCredentialError("Confluence")

        batch = self._fetch_pages(self.confluence_client, start_ind)
        for page in batch:
            last_modified_str = page["version"]["when"]
            author = cast(str | None, page["version"].get("by", {}).get("email"))
            if last_modified_str.endswith('Z'):
                last_modified_str = last_modified_str[:-1] + '+00:00'
            last_modified = datetime.fromisoformat(last_modified_str)

            if last_modified.tzinfo is None:
                # If no timezone info, assume it is UTC
                last_modified = last_modified.replace(tzinfo=timezone.utc)
            else:
                # If not in UTC, translate it
                last_modified = last_modified.astimezone(timezone.utc)

            if time_filter is None or time_filter(last_modified):
                page_id = page["id"]
                if self.labels_to_skip or not CONFLUENCE_CONNECTOR_SKIP_LABEL_INDEXING:
                    page_labels = self._fetch_labels(self.confluence_client, page_id)

                # check disallowed labels
                if self.labels_to_skip:
                    label_intersection = self.labels_to_skip.intersection(page_labels)
                    if label_intersection:
                        logger.info(
                            f"Page with ID '{page_id}' has a label which has been "
                            f"designated as disallowed: {label_intersection}. Skipping."
                        )
                        continue

                page_html = (
                    page["body"]
                    .get("storage", page["body"].get("view", {}))
                    .get("value")
                )
                page_url = self.wiki_base + page["_links"]["webui"]
                if not page_html:
                    logger.debug("Page is empty, skipping: %s", page_url)
                    continue
                page_text = parse_html_page(page_html, self.confluence_client)

                files_in_used = get_used_attachments(page_html, self.confluence_client)
                attachment_text = self._fetch_attachments(
                    self.confluence_client, page_id, files_in_used
                )
                page_text += attachment_text
                comments_text = self._fetch_comments(self.confluence_client, page_id)
                page_text += comments_text

                doc_metadata: dict[str, str | list[str]] = {
                    "Wiki Space Name": self.space
                }
                if not CONFLUENCE_CONNECTOR_SKIP_LABEL_INDEXING and page_labels:
                    doc_metadata["labels"] = page_labels

                doc_batch.append(
                    Document(
                        id=page_url,
                        sections=[Section(link=page_url, text=page_text)],
                        source=DocumentSource.CONFLUENCE,
                        semantic_identifier=page["title"],
                        doc_updated_at=last_modified,
                        primary_owners=[BasicExpertInfo(email=author)]
                        if author
                        else None,
                        metadata=doc_metadata,
                    )
                )
        return doc_batch, len(batch)

    def load_from_state(self) -> GenerateDocumentsOutput:
        if self.confluence_client is None:
            raise ConnectorMissingCredentialError("Confluence")

        start_ind = 0
        while True:
            doc_batch, num_pages = self._get_doc_batch(start_ind)
            start_ind += num_pages
            if doc_batch:
                yield doc_batch

            if num_pages < self.batch_size:
                break

    def poll_source(
            self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch
    ) -> GenerateDocumentsOutput:
        if self.confluence_client is None:
            raise ConnectorMissingCredentialError("Confluence")

        start_time = datetime.fromtimestamp(start, tz=timezone.utc)
        end_time = datetime.fromtimestamp(end, tz=timezone.utc)

        start_ind = 0
        while True:
            doc_batch, num_pages = self._get_doc_batch(
                start_ind, time_filter=lambda t: start_time <= t <= end_time
            )
            start_ind += num_pages
            if doc_batch:
                yield doc_batch

            if num_pages < self.batch_size:
                break


if __name__ == "__main__":
    connector = ConfluenceConnector(os.environ["CONFLUENCE_TEST_SPACE_URL"])
    connector.load_credentials(
        {
            "confluence_username": os.environ["CONFLUENCE_USER_NAME"],
            "confluence_access_token": os.environ["CONFLUENCE_ACCESS_TOKEN"],
        }
    )
    document_batches = connector.load_from_state()
    print(next(document_batches))
