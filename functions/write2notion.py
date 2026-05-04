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


def write_to_notion(question, ip, answer=""):
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
        "properties": {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": "chat log"
                        }
                    }
                ]
            },
            "questions": {
                "rich_text": [
                    {
                        "text": {
                            "content": question
                        }
                    }
                ]
            },
            "answer": {
                "rich_text": [
                    {
                        "text": {
                            "content": answer
                        }
                    }
                ]
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
    }

    res = requests.post(url, json=data, headers=headers)

    print("Status:", res.status_code)
    print("Response:", res.json())


if __name__ == "__main__":
    write_to_notion("test", "127.0.0.1", "test answer")