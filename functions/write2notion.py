import datetime
import os
from zoneinfo import ZoneInfo

import requests

try:
    from functions.env_loader import load_env
except ModuleNotFoundError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from functions.env_loader import load_env


def _get_notion_settings() -> tuple[str, str]:
    load_env()

    token = os.getenv("NOTION_TOKEN", "").strip()
    database_id = os.getenv("DATABASE_ID", os.getenv("NOTION_DATABASE_ID", "")).strip()
    return token, database_id


def _rich_text_or_empty(value: str) -> list:
    text = (value or "").strip()
    if not text:
        return []
    return [{"text": {"content": text}}]


def _build_notion_payload(
    question: str,
    ip: str,
    answer: str,
    app_name: str,
    token_input: int | None,
    token_output: int | None,
    token_mode: str,
) -> dict:
    properties = {
        "Title": {
            "title": [
                {
                    "text": {
                        "content": "chat log"
                    }
                }
            ]
        },
        "App name": {
            "rich_text": [
                {
                    "text": {
                        "content": app_name
                    }
                }
            ]
        },
        "questions": {
            "rich_text": _rich_text_or_empty(question)
        },
        "answer": {
            "rich_text": _rich_text_or_empty(answer)
        },
        "ip address": {
            "rich_text": [
                {
                    "text": {
                        "content": ip
                    }
                }
            ]
        },
        "datetime": {
            "date": {
                "start": datetime.datetime.now(ZoneInfo("Europe/Paris")).isoformat()
            }
        }
    }

    if token_mode == "number":
        properties["token_input"] = {"number": token_input}
        properties["token_output"] = {"number": token_output}
    else:
        token_input_text = "" if token_input is None else str(token_input)
        token_output_text = "" if token_output is None else str(token_output)
        properties["token_input"] = {"rich_text": _rich_text_or_empty(token_input_text)}
        properties["token_output"] = {"rich_text": _rich_text_or_empty(token_output_text)}

    return {
        "properties": properties
    }


def write_to_notion(
    question,
    ip,
    answer="",
    app_name="TSU_LLM_AIUseCase",
    token_input: int | None = None,
    token_output: int | None = None,
):
    notion_token, database_id = _get_notion_settings()
    if not notion_token or not database_id:
        raise ValueError("Missing Notion credentials. Set NOTION_TOKEN and DATABASE_ID in the environment.")

    url = "https://api.notion.com/v1/pages"

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    data = {
        "parent": {"database_id": database_id},
        **_build_notion_payload(
            question,
            ip,
            answer,
            app_name,
            token_input,
            token_output,
            token_mode="number",
        ),
    }

    res = requests.post(url, json=data, headers=headers)
    if res.status_code >= 300:
        # Fallback in case token fields are configured as rich_text.
        fallback_data = {
            "parent": {"database_id": database_id},
            **_build_notion_payload(
                question,
                ip,
                answer,
                app_name,
                token_input,
                token_output,
                token_mode="rich_text",
            ),
        }
        fallback_res = requests.post(url, json=fallback_data, headers=headers)
        if fallback_res.status_code >= 300:
            raise RuntimeError(f"Notion write failed: {fallback_res.status_code} {fallback_res.text}")
        return

    return


if __name__ == "__main__":
    write_to_notion("test", "127.0.0.1", "test answer")