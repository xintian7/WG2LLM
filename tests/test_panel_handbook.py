import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from functions import handbook


APP_PATH = Path(__file__).resolve().parent.parent / "app_wp2llm.py"
HANDBOOK_AVAILABLE = handbook.HANDBOOK_PATH.is_file()


def _section_markup(app):
    return next(
        (item.value for item in app.markdown if 'class="wgii-handbook"' in item.value),
        None,
    )


@unittest.skipUnless(HANDBOOK_AVAILABLE, "userhandbook/sections-11-5-11-6.html is not present")
class HandbookPanelTests(unittest.TestCase):
    def test_principles_button_shows_section_11_5_only(self):
        app = AppTest.from_file(str(APP_PATH)).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.button(key="main_btn_principles").label, "WGII's AI principles 📜")
        self.assertNotIn("Report new use cases 📝", [button.label for button in app.button])

        app.button(key="main_btn_principles").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["active_panel"], "ai_principles")
        markup = _section_markup(app)
        self.assertIn('id="section-11-5">11.5 Use of Artificial Intelligence in the Assessment', markup)
        self.assertLess(markup.index("Last update: 24-11-2026"), markup.index('id="section-11-5"'))
        self.assertIn("<td>AI PoC</td>", markup)
        self.assertNotIn('id="section-11-6"', markup)
        self.assertEqual(markup.count("Last update:"), 1)
        self.assertNotIn("creating summaries", markup.lower())
        self.assertNotIn("assessment texts or summaries", markup.lower())
        guidance, _ = handbook.load_handbook_guidance()
        self.assertNotIn("creating summaries", guidance.lower())
        self.assertNotIn("assessment texts or summaries", guidance.lower())
        self.assertIn("Creating preliminary summaries to support the assessment", guidance)

    def test_reference_button_shows_section_11_6_only(self):
        app = AppTest.from_file(str(APP_PATH)).run()
        app.button(key="main_btn_reference").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["active_panel"], "view_use_cases")
        markup = _section_markup(app)
        self.assertIn('id="section-11-6">11.6 AI Use Case Reference', markup)
        self.assertLess(markup.index("Last update: 24-11-2026"), markup.index('id="section-11-6"'))
        self.assertIn("internal data visualization", markup)
        self.assertNotIn('id="section-11-5"', markup)
        self.assertEqual(markup.count("Last update:"), 1)
        self.assertNotIn("How do we use AI responsibly?", markup)
        self.assertEqual(len(app.get("download_button")), 0)
        self.assertFalse(any(button.label == "Expand to full screen" for button in app.button))

    def test_sections_have_no_blank_lines_that_break_html_rendering(self):
        for section in ("11.5", "11.6"):
            with self.subTest(section=section):
                html = handbook.load_handbook_section(section)
                self.assertNotIn("\n\n", html)
                self.assertTrue(html.rstrip().endswith("</section>"))

    def test_use_case_table_shrinks_to_fit_and_scrolls_only_when_narrow(self):
        html = handbook.load_handbook_section("11.6")
        self.assertNotIn("min-width: 800px", html)
        self.assertIn("#use-case-reference { min-width: 0;", html)
        self.assertIn("container: wgii-handbook / inline-size;", html)
        self.assertIn("@container wgii-handbook (max-width: 620px)", html)

    def test_principles_display_in_one_row_below_title(self):
        html = handbook.load_handbook_section("11.6")
        self.assertIn('class="principles-title">Key Principles for Responsible AI Use', html)
        self.assertEqual(html.count('class="principle"'), 4)
        self.assertIn(
            ".principles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));",
            html,
        )
        self.assertIn(".principles-title { grid-column: 1 / -1;", html)
        self.assertIn("overflow-wrap: anywhere;", html)


class HandbookErrorTests(unittest.TestCase):
    def test_missing_handbook_shows_an_error(self):
        for renderer, expected in (
            ("panel_ai_principles import render_ai_principles", "Could not load WGII's AI principles"),
            ("panel_reference import render_ai_use_case_reference", "Could not load the AI use case reference"),
        ):
            with self.subTest(renderer=renderer), patch.object(
                handbook, "HANDBOOK_PATH", Path("/nonexistent/handbook.html")
            ):
                name = renderer.split(" import ")[1]
                app = AppTest.from_string(
                    f"from functions.{renderer}\n{name}()\n"
                ).run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.error), 1)
                self.assertIn(expected, app.error[0].value)

    def test_feedback_remains_available_for_new_use_cases(self):
        app = AppTest.from_file(str(APP_PATH))
        app.query_params["page"] = "feedback"
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_area[0].label, "Question or suggestion *")


class MainPanelLayoutTests(unittest.TestCase):
    def test_all_panels_use_the_same_responsive_width(self):
        app = AppTest.from_file(str(APP_PATH)).run()
        for key, panel in (
            ("main_btn_ai_guidance", "ai_guidance"),
            ("main_btn_rephrase", "rephrase"),
            ("main_btn_grammar", "grammar"),
            ("main_btn_principles", "ai_principles"),
            ("main_btn_reference", "view_use_cases"),
            ("main_btn_analysis", "use_case_scenario_analysis"),
        ):
            with self.subTest(panel=panel):
                app.button(key=key).click().run()
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state["active_panel"], panel)
                styles = [
                    item.value
                    for item in app.markdown
                    if 'div[data-testid="stMainBlockContainer"]' in item.value
                ]
                self.assertEqual(len(styles), 1)
                self.assertIn("max-width: 60vw !important;", styles[0])
                self.assertIn("@media (max-width: 700px)", styles[0])
                self.assertIn("max-width: 100vw !important;", styles[0])


if __name__ == "__main__":
    unittest.main()
