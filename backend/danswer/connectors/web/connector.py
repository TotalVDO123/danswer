import io
from collections.abc import Generator
from typing import Any
from typing import cast
from urllib.parse import urljoin
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from danswer.configs.app_configs import INDEX_BATCH_SIZE
from danswer.configs.constants import DocumentSource
from danswer.configs.constants import HTML_SEPARATOR
from danswer.connectors.interfaces import LoadConnector
from danswer.connectors.models import Document
from danswer.connectors.models import Section
from danswer.utils.logging import setup_logger
from playwright.sync_api import sync_playwright
from PyPDF2 import PdfReader

logger = setup_logger()


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_internal_links(
    base_url: str, url: str, soup: BeautifulSoup, should_ignore_pound: bool = True
) -> list[str]:
    internal_links = []
    for link in cast(list[dict[str, Any]], soup.find_all("a")):
        href = cast(str | None, link.get("href"))
        if not href:
            continue

        if should_ignore_pound and "#" in href:
            href = href.split("#")[0]

        if not is_valid_url(href):
            # Relative path handling
            if url[-1] != "/":
                url += "/"
            href = urljoin(url, href)

        if urlparse(href).netloc == urlparse(url).netloc and base_url in href:
            internal_links.append(href)
    return internal_links


class WebConnector(LoadConnector):
    def __init__(
        self,
        base_url: str,
        batch_size: int = INDEX_BATCH_SIZE,
    ) -> None:
        self.base_url = base_url
        self.batch_size = batch_size

    def load_from_state(self) -> Generator[list[Document], None, None]:
        """Traverses through all pages found on the website
        and converts them into documents"""
        visited_links: set[str] = set()
        to_visit: list[str] = [self.base_url]
        doc_batch: list[Document] = []

        # Edge case handling user provides HTML without terminating slash (prevents duplicate)
        # Most sites either redirect no slash to slash or serve same content
        if self.base_url[-1] != "/":
            visited_links.add(self.base_url + "/")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()

            while to_visit:
                current_url = to_visit.pop()
                if current_url in visited_links:
                    continue
                visited_links.add(current_url)

                try:
                    if current_url.split(".")[-1] == "pdf":
                        # PDF files are not checked for links
                        response = requests.get(current_url)
                        pdf_reader = PdfReader(io.BytesIO(response.content))
                        page_text = ""
                        for pdf_page in pdf_reader.pages:
                            page_text += pdf_page.extract_text()

                        doc_batch.append(
                            Document(
                                id=current_url,
                                sections=[Section(link=current_url, text=page_text)],
                                source=DocumentSource.WEB,
                                semantic_identifier=current_url.split(".")[-1],
                                metadata={},
                            )
                        )
                        continue

                    page = context.new_page()
                    page.goto(current_url)
                    content = page.content()
                    soup = BeautifulSoup(content, "html.parser")

                    internal_links = get_internal_links(
                        self.base_url, current_url, soup
                    )
                    for link in internal_links:
                        if link not in visited_links:
                            to_visit.append(link)

                    title_tag = soup.find("title")
                    title = None
                    if title_tag and title_tag.text:
                        title = title_tag.text

                    # Heuristics based cleaning
                    for undesired_div in ["sidebar", "header", "footer"]:
                        [
                            tag.extract()
                            for tag in soup.find_all(
                                "div", class_=lambda x: x and undesired_div in x.split()
                            )
                        ]

                    for undesired_tag in [
                        "nav",
                        "header",
                        "footer",
                        "meta",
                        "script",
                        "style",
                    ]:
                        [tag.extract() for tag in soup.find_all(undesired_tag)]

                    page_text = soup.get_text(HTML_SEPARATOR)

                    doc_batch.append(
                        Document(
                            id=current_url,
                            sections=[Section(link=current_url, text=page_text)],
                            source=DocumentSource.WEB,
                            semantic_identifier=title,
                            metadata={},
                        )
                    )

                    page.close()
                except Exception as e:
                    logger.error(f"Failed to fetch '{current_url}': {e}")
                    continue

                if len(doc_batch) >= self.batch_size:
                    yield doc_batch
                    doc_batch = []

            if doc_batch:
                yield doc_batch
