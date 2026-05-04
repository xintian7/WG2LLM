"""UI helper for checking AI use cases via shared QA function."""

from pathlib import Path
import sys

import streamlit as st

from func_OpenAI_query import _cli_main
from functions.env_loader import get_azure_settings


_GUIDANCE_MD = Path(__file__).parent / "AIGuidance_20260428.md.enc"


def get_ai_guidance_status() -> dict:
    """Return guidance availability status for UI display."""
    if not _GUIDANCE_MD.exists():
        return {
            "ready": False,
            "chunks": 0,
            "cached": False,
            "last_load_sec": None,
            "message": f"Guidance file not found: {_GUIDANCE_MD.name}",
        }

    token = _GUIDANCE_MD.read_bytes().strip()
    if not token:
        return {
            "ready": False,
            "chunks": 0,
            "cached": False,
            "last_load_sec": None,
            "message": f"Guidance file is empty: {_GUIDANCE_MD.name}",
        }

    settings = get_azure_settings()
    if not (settings.get("fernet_key") or "").strip():
        return {
            "ready": False,
            "chunks": 0,
            "cached": False,
            "last_load_sec": None,
            "message": "FERNET_KEY is not set in environment.",
        }

    return {
        "ready": True,
        "chunks": 1,
        "cached": False,
        "last_load_sec": None,
        "message": "Guidance markdown loaded.",
    }


def answer_ai_case_question(question: str) -> str:
    """Return an answer for a user AI-use-case question."""
    return _cli_main(question)


def perform_check_aicase(
    query: str,
    container,
) -> str:
    """Run AI use case check for a UI submit event.

    func_OpenAI_query handles connection setting resolution internally.
    """
    question = (query or "").strip()
    if not question:
        container.warning("Please enter a question before submitting.")
        return ""

    if not _GUIDANCE_MD.exists():
        container.error(f"Guidance file is missing: {_GUIDANCE_MD.name}")
        return ""

    with container:
        with st.spinner("Checking AI use case..."):
            try:
                answer = answer_ai_case_question(question)
                st.session_state["ai_case_last_query"] = question
                st.session_state["ai_case_result_box"] = (
                    answer or "No answer content was returned by Azure OpenAI."
                )
                st.caption(f"Question: {st.session_state['ai_case_last_query']}")
                st.text_area(
                    "AI Use Case Result",
                    height=220,
                    key="ai_case_result_box",
                )
                return answer or ""
            except Exception as exc:
                st.error(str(exc))
                return ""


def perform_ai_guidance(
    query: str,
    container,
) -> str:
    """Compatibility wrapper used by existing app wiring."""
    return perform_check_aicase(
        query=query,
        container=container,
    )


def main(test_question: str) -> int:
    """Run terminal smoke test for this module."""
    try:
        print(answer_ai_case_question(test_question))
        return 0
    except Exception as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    question = "Can I use openai to draft the IPCC reports?"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip() or question
    sys.exit(main(question))
