import json
from typing import Any

from openai import OpenAI

from app.core.config import settings

client = OpenAI(
    api_key=settings.openai_api_key,
    timeout=settings.openai_timeout_seconds,
)


def generate_json(prompt: str) -> dict[str, Any]:
    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
        text={
            "format": {
                "type": "json_object",
            }
        },
    )

    return json.loads(response.output_text)


def generate_search_suggestion_json(prompt: str) -> dict[str, Any]:
    return generate_json(prompt)


def generate_rerank_json(prompt: str) -> dict[str, Any]:
    return generate_json(prompt)


def generate_top3_compare_json(prompt: str) -> dict[str, Any]:
    return generate_json(prompt)


def generate_program_reason_json(prompt: str) -> dict[str, Any]:
    return generate_json(prompt)


def generate_review_keywords_json(prompt: str) -> dict[str, Any]:
    return generate_json(prompt)


def generate_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
    )

    if not response.data:
        raise RuntimeError("OpenAI embedding response is empty.")

    return response.data[0].embedding
