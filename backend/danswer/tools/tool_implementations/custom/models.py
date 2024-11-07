from datetime import datetime
from enum import Enum
from typing import Any
from typing import List

from pydantic import BaseModel

CUSTOM_TOOL_RESPONSE_ID = "custom_tool_response"


class CustomToolResponseType(Enum):
    IMAGE = "image"
    CSV = "csv"
    JSON = "json"
    SEARCH = "search"


class CustomToolFileResponse(BaseModel):
    file_ids: List[str]  # References to saved images or CSVs


class CustomToolCallSummary(BaseModel):
    tool_name: str
    response_type: CustomToolResponseType
    tool_result: Any  # The response data


class CustomToolSearchResult(BaseModel):
    content: str
    document_id: str
    semantic_identifier: str
    blurb: str
    link: str | None = None
    updated_at: datetime | None = None


class CustomToolSearchResponse(BaseModel):
    results: List[CustomToolSearchResult]
