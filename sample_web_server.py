import datetime
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class CustomToolSearchResult(BaseModel):
    content: str
    document_id: str
    semantic_identifier: str
    blurb: str
    source_type: str
    score: float
    link: Optional[str] = None
    updated_at: Optional[datetime.datetime] = None


@app.get("/search")
def search_api(query: str):
    # Simulate search results
    results = [
        {
            "content": "This is the content of document 1.",
            "document_id": "doc1",
            "semantic_identifier": "Document 1",
            "blurb": "A brief summary of document 1.",
            "source_type": "local",
            "score": 0.95,
            "link": "http://example.com/doc1",
            "updated_at": datetime.datetime.now().isoformat(),
        },
        {
            "content": "Content of document 2.",
            "document_id": "doc2",
            "semantic_identifier": "Document 2",
            "blurb": "Summary of document 2.",
            "source_type": "local",
            "score": 0.90,
            "link": "http://example.com/doc2",
            "updated_at": datetime.datetime.now().isoformat(),
        },
    ]
    return results


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
