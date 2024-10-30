from collections.abc import Iterator
from datetime import datetime

from googleapiclient.discovery import Resource  # type: ignore

from danswer.connectors.google_drive.constants import DRIVE_FOLDER_TYPE
from danswer.connectors.google_drive.constants import DRIVE_SHORTCUT_TYPE
from danswer.connectors.google_drive.constants import FILE_FIELDS
from danswer.connectors.google_drive.constants import FOLDER_FIELDS
from danswer.connectors.google_drive.constants import SLIM_FILE_FIELDS
from danswer.connectors.google_drive.google_utils import execute_paginated_retrieval
from danswer.connectors.google_drive.models import GoogleDriveFileType
from danswer.connectors.interfaces import SecondsSinceUnixEpoch
from danswer.utils.logger import setup_logger

logger = setup_logger()


def _generate_time_range_filter(
    time_range_start: SecondsSinceUnixEpoch | None = None,
    time_range_end: SecondsSinceUnixEpoch | None = None,
) -> str:
    time_range_filter = ""
    if time_range_start is not None:
        time_start = datetime.utcfromtimestamp(time_range_start).isoformat() + "Z"
        time_range_filter += f" and modifiedTime >= '{time_start}'"
    if time_range_end is not None:
        time_stop = datetime.utcfromtimestamp(time_range_end).isoformat() + "Z"
        time_range_filter += f" and modifiedTime <= '{time_stop}'"
    return time_range_filter


def _get_folders_in_parent(
    service: Resource,
    parent_id: str | None = None,
    personal_drive: bool = False,
) -> Iterator[GoogleDriveFileType]:
    # Follow shortcuts to folders
    query = f"(mimeType = '{DRIVE_FOLDER_TYPE}' or mimeType = '{DRIVE_SHORTCUT_TYPE}')"

    if parent_id:
        query += f" and '{parent_id}' in parents"

    for file in execute_paginated_retrieval(
        retrieval_function=service.files().list,
        list_key="files",
        corpora="user" if personal_drive else "allDrives",
        supportsAllDrives=not personal_drive,
        includeItemsFromAllDrives=not personal_drive,
        fields=FOLDER_FIELDS,
        q=query,
    ):
        yield file


def _get_files_in_parent(
    service: Resource,
    parent_id: str,
    personal_drive: bool,
    time_range_start: SecondsSinceUnixEpoch | None = None,
    time_range_end: SecondsSinceUnixEpoch | None = None,
    is_slim: bool = False,
) -> Iterator[GoogleDriveFileType]:
    query = f"mimeType != '{DRIVE_FOLDER_TYPE}' and '{parent_id}' in parents"
    query += _generate_time_range_filter(time_range_start, time_range_end)

    for file in execute_paginated_retrieval(
        retrieval_function=service.files().list,
        list_key="files",
        corpora="user" if personal_drive else "allDrives",
        supportsAllDrives=not personal_drive,
        includeItemsFromAllDrives=not personal_drive,
        fields=SLIM_FILE_FIELDS if is_slim else FILE_FIELDS,
        q=query,
    ):
        yield file


_TRAVERSED_PARENT_IDS: set[str] = set()


def crawl_folders_for_files(
    service: Resource,
    parent_id: str,
    personal_drive: bool,
    time_range_start: SecondsSinceUnixEpoch | None = None,
    time_range_end: SecondsSinceUnixEpoch | None = None,
) -> Iterator[GoogleDriveFileType]:
    """
    This one can start crawling from any folder. It is slower though.
    """
    if parent_id in _TRAVERSED_PARENT_IDS:
        logger.debug(f"Skipping subfolder since already traversed: {parent_id}")
        return

    _TRAVERSED_PARENT_IDS.add(parent_id)

    yield from _get_files_in_parent(
        service=service,
        personal_drive=personal_drive,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        parent_id=parent_id,
    )

    for subfolder in _get_folders_in_parent(
        service=service,
        parent_id=parent_id,
        personal_drive=personal_drive,
    ):
        logger.info("Fetching all files in subfolder: " + subfolder["name"])
        yield from crawl_folders_for_files(
            service=service,
            parent_id=subfolder["id"],
            personal_drive=personal_drive,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
        )


def get_files_in_shared_drive(
    service: Resource,
    drive_id: str,
    is_slim: bool = False,
    time_range_start: SecondsSinceUnixEpoch | None = None,
    time_range_end: SecondsSinceUnixEpoch | None = None,
) -> Iterator[GoogleDriveFileType]:
    query = f"mimeType != '{DRIVE_FOLDER_TYPE}'"
    query += _generate_time_range_filter(time_range_start, time_range_end)
    for file in execute_paginated_retrieval(
        retrieval_function=service.files().list,
        list_key="files",
        corpora="drive",
        drive_id=drive_id,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        fields=FILE_FIELDS if is_slim else SLIM_FILE_FIELDS,
        q=query,
    ):
        yield file


def get_files_in_my_drive(
    service: Resource,
    email: str,
    is_slim: bool = False,
    time_range_start: SecondsSinceUnixEpoch | None = None,
    time_range_end: SecondsSinceUnixEpoch | None = None,
) -> Iterator[GoogleDriveFileType]:
    query = f"mimeType != '{DRIVE_FOLDER_TYPE}' and '{email}' in owners"
    query += _generate_time_range_filter(time_range_start, time_range_end)
    for file in execute_paginated_retrieval(
        retrieval_function=service.files().list,
        list_key="files",
        corpora="user",
        fields=FILE_FIELDS if is_slim else SLIM_FILE_FIELDS,
        q=query,
    ):
        yield file


# Just in case we need to get the root folder id
def get_root_folder_id(service: Resource) -> str:
    # we dont paginate here because there is only one root folder per user
    # https://developers.google.com/drive/api/guides/v2-to-v3-reference
    return service.files().get(fileId="root", fields="id").execute()["id"]
