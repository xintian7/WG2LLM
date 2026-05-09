import difflib
import html
import json
import re
from typing import Callable

import streamlit as st
import streamlit.components.v1 as components
from openai import AzureOpenAI

from functions.env_loader import get_azure_settings
from functions.func_OpenAI_query import DEFAULT_MODEL
from functions.write2notion import write_to_notion


def _count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


def _highlight_changes(original_text: str, corrected_text: str) -> str:
    token_pattern = r"\w+|[^\w\s]|\s+"
    original_tokens = re.findall(token_pattern, original_text or "")
    corrected_tokens = re.findall(token_pattern, corrected_text or "")

    matcher = difflib.SequenceMatcher(a=original_tokens, b=corrected_tokens)
    output_parts: list[str] = []

    for op, _a0, _a1, b0, b1 in matcher.get_opcodes():
        chunk = "".join(corrected_tokens[b0:b1])
        if op != "equal" and not chunk:
            continue
        escaped_chunk = html.escape(chunk)
        if op == "equal":
            output_parts.append(escaped_chunk)
        else:
            output_parts.append(f"<mark>{escaped_chunk}</mark>")

    return "".join(output_parts)


def _render_output_box(content_html: str) -> None:
    st.markdown(
        (
            "<div style='height: 260px; overflow-y: auto; padding: 0.75rem; border: 1px solid #d9d9d9; "
            "border-radius: 0.5rem; background: #ffffff; line-height: 1.6; "
            "font-family: Source Sans Pro, sans-serif; font-size: 1rem; "
            "white-space: pre-wrap; word-break: break-word;'>"
            f"{content_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def _correct_grammar_with_ai(text: str) -> tuple[bool, str, int | None, int | None]:
    settings = get_azure_settings()
    client = AzureOpenAI(
        api_version=settings.get("api_version") or "2024-12-01-preview",
        azure_endpoint=settings.get("endpoint") or "",
        api_key=settings.get("api_key") or "",
    )

    system_prompt = (
        "You are an English grammar correction assistant. "
        "If the user input is not English, respond exactly with: __NON_ENGLISH__. "
        "If it is English, correct only grammar, spelling, punctuation, and agreement errors. "
        "Keep the original meaning, tone, and structure as much as possible. "
        "Return only the corrected text without explanations or extra markup."
    )

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text.strip()},
        ],
        model=DEFAULT_MODEL,
        temperature=0.0,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        max_completion_tokens=3000,
    )

    corrected = (response.choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    token_input = getattr(usage, "prompt_tokens", None) if usage is not None else None
    token_output = getattr(usage, "completion_tokens", None) if usage is not None else None
    if not isinstance(token_input, int):
        token_input = None
    if not isinstance(token_output, int):
        token_output = None

    if corrected == "__NON_ENGLISH__":
        return False, "Please input English text only.", token_input, token_output

    return True, corrected, token_input, token_output


def render_grammar_panel(get_client_ip: Callable[[], str]) -> None:
    st.divider()
    st.markdown("<h3 style='text-align:center'>Check grammar</h3>", unsafe_allow_html=True)
    st.markdown("Input English text (up to 3000 words) and receive a grammar-corrected version with highlighted changes.")

    input_text = st.text_area(
        "Input text (English only, max 3000 words)",
        key="grammar_input_text",
        value="",
        height=260,
    )
    current_word_count = _count_words(input_text)
    st.caption(f"Word count: {current_word_count} / 3000")
    share_grammar_with_tsu = st.checkbox(
        "Share my prompts and results with TSU for App improvement (optional)",
        key="grammar_share_prompt",
        value=True,
    )

    if st.button("Correct grammar", key="grammar_correct_submit", type="primary"):
        if not input_text.strip():
            st.error("Please enter text to check grammar.")
        elif current_word_count > 3000:
            st.error("Input is too long. Please limit to 3000 words.")
        else:
            with st.spinner("Checking grammar..."):
                try:
                    ok, corrected_text_or_msg, token_input, token_output = _correct_grammar_with_ai(input_text)
                except Exception as exc:
                    st.error(f"Grammar check failed: {exc}")
                    ok = False
                    corrected_text_or_msg = ""
                    token_input = None
                    token_output = None

            if ok:
                corrected_text = corrected_text_or_msg
                if input_text.strip():
                    try:
                        question_to_log = input_text if share_grammar_with_tsu else ""
                        answer_to_log = corrected_text if share_grammar_with_tsu else ""
                        write_to_notion(
                            question_to_log,
                            get_client_ip(),
                            answer_to_log,
                            app_name="TSU_LLM_grammar",
                            token_input=token_input,
                            token_output=token_output,
                        )
                    except Exception as exc:
                        st.warning(f"Notion logging failed: {exc}")
                tab_corrected, tab_highlighted = st.tabs(["Corrected text", "Highlighted changes"])

                with tab_corrected:
                    corrected_html = html.escape(corrected_text)
                    _render_output_box(corrected_html)

                    copy_payload = json.dumps(corrected_text)
                    components.html(
                        f"""
                        <button id=\"copy-corrected-text-btn\" style=\"
                            background:#1f77b4;
                            color:#fff;
                            border:1px solid #1f77b4;
                            border-radius:6px;
                            padding:6px 10px;
                            font-size:13px;
                            cursor:pointer;
                        \">Copy text</button>
                        <script>
                          const btn = document.getElementById('copy-corrected-text-btn');
                          btn.addEventListener('click', async () => {{
                            try {{
                              await navigator.clipboard.writeText({copy_payload});
                              btn.innerText = 'Copied';
                              setTimeout(() => btn.innerText = 'Copy text', 1200);
                            }} catch (e) {{
                              btn.innerText = 'Copy failed';
                              setTimeout(() => btn.innerText = 'Copy text', 1200);
                            }}
                          }});
                        </script>
                        """,
                        height=42,
                    )

                with tab_highlighted:
                    highlighted = _highlight_changes(input_text, corrected_text)
                    _render_output_box(highlighted)

                    highlighted_copy_payload = json.dumps(corrected_text)
                    components.html(
                        f"""
                        <button id=\"copy-highlighted-text-btn\" style=\"
                            background:#1f77b4;
                            color:#fff;
                            border:1px solid #1f77b4;
                            border-radius:6px;
                            padding:6px 10px;
                            font-size:13px;
                            cursor:pointer;
                        \">Copy text</button>
                        <script>
                          const btn = document.getElementById('copy-highlighted-text-btn');
                          btn.addEventListener('click', async () => {{
                            try {{
                              await navigator.clipboard.writeText({highlighted_copy_payload});
                              btn.innerText = 'Copied';
                              setTimeout(() => btn.innerText = 'Copy text', 1200);
                            }} catch (e) {{
                              btn.innerText = 'Copy failed';
                              setTimeout(() => btn.innerText = 'Copy text', 1200);
                            }}
                          }});
                        </script>
                        """,
                        height=42,
                    )
            else:
                st.error(corrected_text_or_msg)
