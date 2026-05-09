import streamlit as st


def render_main_buttons() -> str | None:
    spacer_left, btn_wrap, spacer_right = st.columns([0.3, 6, 0.3])
    with btn_wrap:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Check AI use cases 🔎", use_container_width=True, type="primary", key="main_btn_ai_guidance"):
                st.session_state["active_panel"] = "ai_guidance"
        with col2:
            if st.button("Rephrase sentences ✍️", use_container_width=True, type="primary", key="main_btn_rephrase"):
                st.session_state["active_panel"] = "rephrase"
        with col3:
            if st.button("Check grammar ✅", use_container_width=True, type="primary", key="main_btn_grammar"):
                st.session_state["active_panel"] = "grammar"

        row2_col1, row2_col2, row2_col3 = st.columns(3)
        with row2_col1:
            if st.button("AI use case reference 📖", use_container_width=True, type="primary", key="main_btn_reference"):
                st.session_state["active_panel"] = "view_use_cases"
        with row2_col2:
            if st.button("Report new use cases 📝", use_container_width=True, type="primary", key="main_btn_report"):
                st.session_state["active_panel"] = "report_use_case"
        with row2_col3:
            if st.button("Use case analysis 🧭", use_container_width=True, type="secondary", key="main_btn_analysis"):
                st.session_state["active_panel"] = "use_case_scenario_analysis"

        st.columns(3)

    return st.session_state.get("active_panel")
