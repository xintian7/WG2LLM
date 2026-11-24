from typing import Callable

import streamlit as st

from functions.env_loader import format_model_label, get_ai_guidance_model
from functions.func_OpenAI_query import query_openai_with_guidance_result
from functions.handbook import load_handbook_guidance
from functions.write2notion import write_to_notion


def get_ai_guidance_status() -> dict:
    """Return guidance availability status for UI display."""
    try:
        load_handbook_guidance()
    except (OSError, UnicodeError, ValueError) as exc:
        return {
            "ready": False,
            "chunks": 0,
            "cached": False,
            "last_load_sec": None,
            "message": f"Could not load handbook guidance: {exc}",
        }

    return {
        "ready": True,
        "chunks": 1,
        "cached": False,
        "last_load_sec": None,
        "message": "Handbook sections 11.5 and 11.6 loaded.",
    }


def _answer_ai_case_question(
    question: str,
    model: str,
    guidance: str,
) -> tuple[str, int | None, int | None]:
    return query_openai_with_guidance_result(question=question, model=model, guidance_text=guidance)


def _append_point_four(answer: str, principles: str) -> str:
    base = _strip_point_four(answer)
    if not base:
        return f"4) AI principles:\n{principles}"

    return f"{base}\n\n4) AI principles:\n{principles}"


def _strip_point_four(answer: str) -> str:
    text = (answer or "").strip()
    if not text:
        return ""

    marker = "\n\n4) AI principles:"
    if marker in text:
        return text.split(marker, 1)[0].rstrip()

    marker_alt = "\n4) AI principles:"
    if marker_alt in text:
        return text.split(marker_alt, 1)[0].rstrip()

    return text


def _format_answer_display(answer: str) -> str:
    text = (answer or "").strip()
    if not text:
        return text

    lines = [line.rstrip() for line in text.splitlines()]
    replacements = {
        "1) Permission category:": "1) **Permission category:**",
        "2) Why:": "2) **Why:**",
        "3) What to pay attention to:": "3) **What to pay attention to:**",
        "4) AI principles:": "4) **AI principles:**",
    }
    formatted = []
    in_bullet_section = False
    for line in lines:
        updated = line
        for needle, repl in replacements.items():
            if needle in updated:
                updated = updated.replace(needle, repl, 1)
                break

        lower_updated = updated.lower().strip()
        if lower_updated.startswith("3) **what to pay attention to:**") or lower_updated.startswith("4) **ai principles:**"):
            in_bullet_section = True
        elif lower_updated.startswith("1)") or lower_updated.startswith("2)"):
            in_bullet_section = False

        # Keep bullets visually nested under numbered sections in Streamlit markdown.
        if in_bullet_section and updated.strip().startswith("-"):
            updated = f"    {updated.strip()}"

        formatted.append(updated)
    return "\n".join(formatted)


def perform_ai_guidance(
    query: str,
    container,
    model: str,
) -> tuple[str, int | None, int | None]:
    question = (query or "").strip()
    if not question:
        container.warning("Please enter a question before submitting.")
        return "", None, None

    with container:
        with st.spinner("Checking AI use case..."):
            try:
                guidance, principles = load_handbook_guidance()
                answer, token_input, token_output = _answer_ai_case_question(question, model=model, guidance=guidance)
                if not answer.strip():
                    raise ValueError("No answer content was returned by Azure OpenAI.")
                answer_with_point_four = _append_point_four(answer or "", principles)
                st.session_state["ai_case_last_query"] = question
                st.session_state["ai_case_result_box"] = (
                    answer_with_point_four or "No answer content was returned by Azure OpenAI."
                )
                st.caption(f"Question: {st.session_state['ai_case_last_query']}")
                st.markdown(_format_answer_display(st.session_state["ai_case_result_box"]))
                return answer_with_point_four or "", token_input, token_output
            except Exception as exc:
                st.error(str(exc))
                return "", None, None


def render_ai_guidance_panel(get_client_ip: Callable[[], str]) -> None:
    st.divider()
    st.markdown("<h3 style='text-align:center'>Check AI use cases based on the AI guidance</h3>", unsafe_allow_html=True)
    ai_guidance_container = st.container()

    with ai_guidance_container:
        kb_status = get_ai_guidance_status()
        if kb_status["ready"]:
            st.caption(f"Knowledge base: ready | {kb_status['message']}")
        else:
            msg = kb_status["message"] or "Knowledge base is not ready yet."
            st.caption(f"Knowledge base: not ready | {msg}")

        try:
            configured_ai_guidance_model = get_ai_guidance_model()
        except ValueError as exc:
            st.error(str(exc))
            return

        user_query = st.text_area(
            "Check whether an AI use case is permitted based on the AI guidance from the WGII AR7 Author Handbook:",
            placeholder="e.g. Can I use AI to help rephrase a sentence in the assessment text?",
            key="ai_guidance_query",
            height=120,
        )
        ai_guidance_model = st.selectbox(
            "Model",
            options=[configured_ai_guidance_model],
            index=0,
            format_func=format_model_label,
            key="ai_guidance_model",
        )
        share_with_tsu = st.checkbox(
            "Share my prompts and results with TSU for App improvement (optional)",
            key="ai_guidance_share_prompt",
            value=True,
        )
        submitted = st.button("Submit", key="ai_guidance_submit", type="primary")

        if submitted:
            answer_text, token_input, token_output = perform_ai_guidance(
                query=user_query,
                container=ai_guidance_container,
                model=ai_guidance_model,
            )
            if user_query.strip():
                try:
                    question_to_log = user_query if share_with_tsu else ""
                    answer_to_log = _strip_point_four(answer_text) if share_with_tsu else ""
                    write_to_notion(
                        question_to_log,
                        get_client_ip(),
                        answer_to_log,
                        app_name=f"TSU_LLM_AIUseCase ({ai_guidance_model})",
                        token_input=token_input,
                        token_output=token_output,
                    )
                except Exception as exc:
                    st.warning(f"Notion logging failed: {exc}")
