from __future__ import annotations

import datetime
import itertools
from collections.abc import Generator
from typing import Any
from typing import ClassVar

import pywikibot.time  # type: ignore[import-untyped]
from pywikibot import pagegenerators  # type: ignore[import-untyped]
from pywikibot import textlib  # type: ignore[import-untyped]

from danswer.configs.app_configs import INDEX_BATCH_SIZE
from danswer.configs.constants import DocumentSource
from danswer.connectors.interfaces import GenerateDocumentsOutput
from danswer.connectors.interfaces import LoadConnector
from danswer.connectors.interfaces import PollConnector
from danswer.connectors.interfaces import SecondsSinceUnixEpoch
from danswer.connectors.mediawiki.family import family_class_dispatch
from danswer.connectors.models import Document
from danswer.connectors.models import Section


def pywikibot_timestamp_to_utc_datetime(
    timestamp: pywikibot.time.Timestamp,
) -> datetime.datetime:
    """Convert a pywikibot timestamp to a datetime object in UTC.

    Args:
        timestamp: The pywikibot timestamp to convert.

    Returns:
        A datetime object in UTC.
    """
    return datetime.datetime.astimezone(timestamp, tz=datetime.timezone.utc)


def get_doc_from_page(
    page: pywikibot.Page, site: pywikibot.Site | None, source_type: DocumentSource
) -> Document:
    """Generate Danswer Document from a MediaWiki page object.

    Args:
        page: Page from a MediaWiki site.
        site: MediaWiki site (used to parse the sections of the page using the site template, if available).
        source_type: Source of the document.

    Returns:
        Generated document.
    """
    page_text = page.text
    sections_extracted: textlib.Content = textlib.extract_sections(page_text, site)

    sections = [
        Section(
            link=f"{page.full_url()}#" + section.heading.replace(" ", "_"),
            text=section.title + section.content,
        )
        for section in sections_extracted.sections
    ]
    sections.append(
        Section(
            link=page.full_url(),
            text=sections_extracted.header,
        )
    )

    return Document(
        source=source_type,
        title=page.title(),
        doc_updated_at=pywikibot_timestamp_to_utc_datetime(
            page.latest_revision.timestamp
        ),
        sections=sections,
        semantic_identifier=page.title(),
        metadata={"categories": [category.title() for category in page.categories()]},
        id=page.pageid,
    )


class MediaWikiConnector(LoadConnector, PollConnector):
    """A connector for MediaWiki wikis.

    Args:
        hostname: The hostname of the wiki.
        categories: The categories to include in the index.
        pages: The pages to include in the index.
        recurse_depth: The depth to recurse into categories. -1 means unbounded recursion.
        language_code: The language code of the wiki.
        batch_size: The batch size for loading documents.

    Raises:
        ValueError: If `recurse_depth` is not an integer greater than or equal to -1.
    """

    document_source_type: ClassVar[DocumentSource] = DocumentSource.MEDIAWIKI
    """DocumentSource type for all documents generated by instances of this class. Can be overridden for connectors
    tailored for specific sites."""

    def __init__(
        self,
        hostname: str,
        categories: list[str],
        pages: list[str],
        recurse_depth: int,
        language_code: str = "en",
        batch_size: int = INDEX_BATCH_SIZE,
    ) -> None:
        if recurse_depth < -1:
            raise ValueError(
                f"recurse_depth must be an integer greater than or equal to -1. Got {recurse_depth} instead."
            )
        # -1 means infinite recursion, which `pywikibot` will only do with `True`
        self.recurse_depth: bool | int = True if recurse_depth == -1 else recurse_depth

        self.batch_size = batch_size

        # short names can only have ascii letters and digits

        self.family = family_class_dispatch(hostname, "Wikipedia Connector")()
        self.site = pywikibot.Site(fam=self.family, code=language_code)
        self.categories = [
            pywikibot.Category(self.site, f"Category:{category.replace(' ', '_')}")
            for category in categories
        ]
        self.pages = [pywikibot.Page(self.site, page) for page in pages]

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        """Load credentials for a MediaWiki site.

        Note:
            For most read-only operations, MediaWiki API credentials are not necessary.
            This method can be overridden in the event that a particular MediaWiki site
            requires credentials.
        """
        return None

    def _get_doc_batch(
        self,
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
    ) -> Generator[list[Document], None, None]:
        """Request batches of pages from a MediaWiki site.

        Args:
            start: The beginning of the time period of pages to request.
            end: The end of the time period of pages to request.

        Yields:
            Lists of Documents containing each parsed page in a batch.
        """
        doc_batch: list[Document] = []

        # Pywikibot can handle batching for us, including only loading page contents when we finally request them.
        category_pages = [
            pagegenerators.PreloadingGenerator(
                pagegenerators.EdittimeFilterPageGenerator(
                    pagegenerators.CategorizedPageGenerator(
                        category, recurse=self.recurse_depth
                    ),
                    last_edit_start=datetime.datetime.fromtimestamp(start)
                    if start
                    else None,
                    last_edit_end=datetime.datetime.fromtimestamp(end) if end else None,
                ),
                groupsize=self.batch_size,
            )
            for category in self.categories
        ]

        # Since we can specify both individual pages and categories, we need to iterate over all of them.
        all_pages = itertools.chain(self.pages, *category_pages)
        for page in all_pages:
            doc_batch.append(
                get_doc_from_page(page, self.site, self.document_source_type)
            )
            if len(doc_batch) >= self.batch_size:
                yield doc_batch
                doc_batch = []
        if doc_batch:
            yield doc_batch

    def load_from_state(self) -> GenerateDocumentsOutput:
        """Load all documents from the source.

        Returns:
            A generator of documents.
        """
        return self.poll_source(None, None)

    def poll_source(
        self, start: SecondsSinceUnixEpoch | None, end: SecondsSinceUnixEpoch | None
    ) -> GenerateDocumentsOutput:
        """Poll the source for new documents.

        Args:
            start: The start of the time range to poll.
            end: The end of the time range to poll.

        Returns:
            A generator of documents.
        """
        return self._get_doc_batch(start, end)


if __name__ == "__main__":
    HOSTNAME = "fallout.fandom.com"
    test_connector = MediaWikiConnector(
        hostname=HOSTNAME,
        categories=["Fallout:_New_Vegas_factions"],
        pages=["Fallout: New Vegas"],
        recurse_depth=1,
    )

    all_docs = list(test_connector.load_from_state())
    print("All docs", all_docs)
    current = datetime.datetime.now().timestamp()
    one_day_ago = current - 30 * 24 * 60 * 60  # 30 days
    latest_docs = list(test_connector.poll_source(one_day_ago, current))
    print("Latest docs", latest_docs)
