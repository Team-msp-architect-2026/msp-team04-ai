import json
from typing import Any

from openai import OpenAI

from app.core.config import settings

client = OpenAI(
    api_key=settings.openai_api_key,
    timeout=settings.openai_timeout_seconds,
)


def generate_search_suggestion_json(prompt: str) -> dict[str, Any]:
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
