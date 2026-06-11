import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_llm_settings() -> dict[str, Any]:
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1"
    model = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    return {
        "base_url": base_url,
        "model": model,
        "has_api_key": bool(api_key),
    }


def call_llm_json(messages: list[dict[str, str]]) -> dict[str, Any]:
    settings = get_llm_settings()

    if not settings["has_api_key"]:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Set it in your .env file or environment."
        )

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=settings["base_url"],
    )

    try:
        response = client.chat.completions.create(
            model=settings["model"],
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3,
        )
    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {e}") from e

    choice = response.choices[0]
    content = choice.message.content

    if not content or not content.strip():
        raise ValueError(
            "OpenAI returned an empty response. "
            f"Finish reason: {choice.finish_reason}"
        )

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"OpenAI returned invalid JSON. Raw output:\n{content}"
        ) from e
