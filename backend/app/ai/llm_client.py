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


def _attempt(
    messages: list[dict[str, str]], use_json_format: bool
) -> dict[str, Any]:
    settings = get_llm_settings()

    kwargs: dict[str, Any] = {
        "model": settings["model"],
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    if use_json_format:
        kwargs["response_format"] = {"type": "json_object"}

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=settings["base_url"],
    )

    response = client.chat.completions.create(**kwargs)

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


def call_llm_json(messages: list[dict[str, str]]) -> dict[str, Any]:
    settings = get_llm_settings()

    if not settings["has_api_key"]:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Set it in your .env file or environment."
        )

    try:
        return _attempt(messages, use_json_format=True)
    except Exception as first_err:
        err_msg = str(first_err).lower()
        is_json_failure = (
            "json" in err_msg
            or "max tokens" in err_msg
            or "max completion tokens" in err_msg
            or "finish reason" in err_msg
            or "invalid" in err_msg
        )
        if not is_json_failure:
            raise RuntimeError(f"OpenAI API call failed: {first_err}") from first_err

        try:
            return _attempt(messages, use_json_format=False)
        except Exception as retry_err:
            raise RuntimeError(
                f"OpenAI retry also failed (original: {first_err}, retry: {retry_err})"
            ) from retry_err
