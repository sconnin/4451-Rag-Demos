"""Break a complex query into simpler, independently-answerable sub-queries."""
import json

from openai import OpenAI

from core.config import MODEL

DECOMPOSE_SCHEMA = {
    "name": "decompose_query",
    "schema": {
        "type": "object",
        "properties": {
            "subqueries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "1-4 simpler, independently-answerable sub-questions",
            }
        },
        "required": ["subqueries"],
        "additionalProperties": False,
    },
    "strict": True,
}


def decompose_query(client: OpenAI, query: str) -> list[str]:
    """Ask the model to break a complex query into simpler sub-queries.

    If the query is already simple/atomic, the model is instructed to return
    it unchanged as the single sub-query.
    """
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_schema", "json_schema": DECOMPOSE_SCHEMA},
        messages=[
            {
                "role": "system",
                "content": (
                    "You decompose a user's question into a small set of simpler, "
                    "independently-answerable sub-questions that together cover the "
                    "original question. If the question is already simple and atomic, "
                    "return it unchanged as the only sub-question. Return at most 4 "
                    "sub-questions."
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    text = response.choices[0].message.content
    data = json.loads(text)
    return data.get("subqueries") or [query]
