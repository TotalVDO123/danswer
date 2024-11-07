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
        CustomToolSearchResult(
            content="""Dogs are known for their loyalty and affection towards humans. 
            They come in various breeds, each with unique characteristics.""",
            document_id="dog1",
            semantic_identifier="Dog Basics",
            blurb="An overview of dogs as pets and their general traits.",
            source_type="Pet Information",
            score=0.95,
            link="http://example.com/dogs/basics",
            updated_at=datetime.datetime.now(),
        ),
        CustomToolSearchResult(
            content="""Cats are independent and often aloof pets.
            They are known for their grooming habits and ability to hunt small prey.""",
            document_id="cat1",
            semantic_identifier="Cat Basics",
            blurb="An introduction to cats as pets and their typical behaviors.",
            source_type="Pet Information",
            score=0.92,
            link="http://example.com/cats/basics",
            updated_at=datetime.datetime.now(),
        ),
        CustomToolSearchResult(
            content="""Hamsters are small rodents that make popular pocket pets.
            They are nocturnal and require a cage with exercise wheels and tunnels.""",
            document_id="hamster1",
            semantic_identifier="Hamster Care",
            blurb="Essential information for keeping hamsters as pets.",
            source_type="Pet Information",
            score=0.88,
            link="http://example.com/hamsters/care",
            updated_at=datetime.datetime.now(),
        ),
    ]
    return results


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


# {
#   "info": {
#     "title": "Sample Search API",
#     "version": "1.0.0",
#     "description": "An API for performing searches and returning sample results"
#   },
#   "paths": {
#     "/search": {
#       "get": {
#         "summary": "Perform a search",
#         "responses": {
#           "200": {
#             "content": {
#               "application/json": {
#                 "schema": {
#                   "type": "array",
#                   "items": {
#                     "$ref": "#/components/schemas/CustomToolSearchResult"
#                   }
#                 }
#               }
#             },
#             "description": "Successful response"
#           }
#         },
#         "parameters": [
#           {
#             "in": "query",
#             "name": "query",
#             "schema": {
#               "type": "string"
#             },
#             "required": true,
#             "description": "The search query"
#           }
#         ],
#         "operationId": "searchApi"
#       }
#     }
#   },
#   "openapi": "3.0.0",
#   "servers": [
#     {
#       "url": "http://localhost:8000"
#     }
#   ],
#   "components": {
#     "schemas": {
#       "CustomToolSearchResult": {
#         "type": "object",
#         "required": [
#           "content",
#           "document_id",
#           "semantic_identifier",
#           "blurb",
#           "source_type",
#           "score"
#         ],
#         "properties": {
#           "link": {
#             "type": "string",
#             "nullable": true
#           },
#           "blurb": {
#             "type": "string"
#           },
#           "content": {
#             "type": "string"
#           },
#           "updated_at": {
#             "type": "string",
#             "format": "date-time",
#             "nullable": true
#           },
#           "document_id": {
#             "type": "string"
#           },
#           "semantic_identifier": {
#             "type": "string"
#           }
#         }
#       }
#     }
#   }
# }
