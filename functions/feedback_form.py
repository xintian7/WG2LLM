import os
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Tuple
from zoneinfo import ZoneInfo

import requests
import streamlit as st

from functions.env_loader import load_env


@dataclass
class FeedbackConfig:
    app_name: str = "TSU_LLM_Feedback"
    form_key: str = "feedback_form"
    title: str = "Give feedback"
    show_divider: bool = False
    center_title: bool = False
    intro_text: str = (
        "Any feedback is welcome! Please share your questions or suggestions below "
        "to help us improve the app. We will review all feedback carefully and get "
        "back to you if you indicate that we can contact you."
    )
    form_instruction_text: str = (
        "Please fill out the form below. Fields marked with * are required."
    )
    required_prompt_label: str = "Question or suggestion *"
    submit_button_label: str = "Submit"
    submit_button_type: str = "secondary"
    timezone_name: str = "Europe/Paris"
    notion_token_env: str = "NOTION_TOKEN"
    notion_database_env: str = "DATABASE_ID_feedback"


def _clean(value: str | None) -> str:
    raw = (value or "").strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
        return raw[1:-1].strip()
    return raw


def submit_feedback_to_notion(
    *,
    name: str,
    chapter: str,
    email: str,
    message: str,
    contact_ok: bool,
    app_name: str,
    notion_token_env: str,
    notion_database_env: str,
    timezone_name: str,
) -> Tuple[bool, str]:
    load_env()
    token = _clean(os.getenv(notion_token_env))
    database_id = _clean(os.getenv(notion_database_env))

    if not token or not database_id:
        return False, "Notion credentials are missing in the environment."

    title_value = name.strip() or "Feedback"
    email_value = email.strip() if email.strip() else None

    try:
        now_iso = datetime.now(ZoneInfo(timezone_name)).isoformat()
    except Exception:
        now_iso = datetime.now().isoformat()

    properties = {
        "Title": {"title": [{"text": {"content": title_value}}]},
        "App name": {"rich_text": [{"text": {"content": app_name}}]},
        "Name": {"rich_text": [{"text": {"content": name.strip()}}]},
        "Chapter": {"rich_text": [{"text": {"content": chapter.strip()}}]},
        "Email": {"email": email_value},
        "Question or Suggestion": {"rich_text": [{"text": {"content": message.strip()}}]},
        "Further Contact": {
            "rich_text": [{"text": {"content": "Yes" if contact_ok else "No"}}]
        },
        "Datetime": {"date": {"start": now_iso}},
    }

    payload = {"parent": {"database_id": database_id}, "properties": properties}

    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
    except requests.RequestException as exc:
        return False, f"Failed to submit feedback to Notion: {exc}"

    if response.status_code >= 300:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        return False, f"Failed to submit feedback to Notion. Response detail: {detail}"

    return True, "Thank you! Your feedback has been submitted."


def render_feedback_form(
    config: FeedbackConfig,
    submitter: Callable[..., Tuple[bool, str]] = submit_feedback_to_notion,
) -> None:
    if config.show_divider:
        st.divider()

    if config.center_title:
        st.markdown(
            f"<h3 style='text-align:center'>{config.title}</h3>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"### {config.title}")

    st.markdown(config.intro_text)
    st.markdown(config.form_instruction_text)

    with st.form(config.form_key):
        name = st.text_input("Name (optional)", value="")
        chapter = st.text_input("Chapter (optional)", value="")
        email = st.text_input(
            "Email address (required if you want to be contacted)",
            value="",
        )
        message = st.text_area(config.required_prompt_label, value="", height=160)
        contact_ok = st.checkbox(
            "I would like to be contacted about this inquiry",
            value=False,
        )
        submitted = st.form_submit_button(
            config.submit_button_label,
            type=config.submit_button_type,
        )

    if not submitted:
        return

    missing = []
    if not message.strip():
        missing.append("Question or suggestion")
    if contact_ok and not email.strip():
        missing.append("Email address")

    email_value = email.strip()
    if email_value and "@" not in email_value:
        st.error("Please enter a valid email address.")
        return

    if missing:
        st.error(f"Please complete the required fields: {', '.join(missing)}.")
        return

    ok, msg = submitter(
        name=name,
        chapter=chapter,
        email=email,
        message=message,
        contact_ok=contact_ok,
        app_name=config.app_name,
        notion_token_env=config.notion_token_env,
        notion_database_env=config.notion_database_env,
        timezone_name=config.timezone_name,
    )

    if ok:
        st.success(msg)
    else:
        st.error(msg)
