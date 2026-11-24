import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from functions import handbook, panel_ai_guidance, func_OpenAI_query
from streamlit.testing.v1 import AppTest


@unittest.skipUnless(handbook.HANDBOOK_PATH.is_file(), "Handbook is not present")
class HandbookGuidanceTests(unittest.TestCase):
    def test_checker_uses_current_sections_and_preserves_template(self):
        guidance, principles = handbook.load_handbook_guidance()
        self.assertIn('id="section-11-5"', guidance)
        self.assertIn('id="section-11-6"', guidance)
        self.assertIn('id="use-case-reference"', guidance)
        self.assertIn('rowspan=', guidance)
        self.assertIn("✓", guidance)
        self.assertIn("✕", guidance)
        self.assertNotIn("<!--", guidance)
        self.assertNotIn("<style>", guidance)
        self.assertEqual(len(principles.splitlines()), 4)
        self.assertIn("Human accountability:", principles)
        self.assertIn("Comprehensiveness:", principles)

        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=(
                "1) Permission category: Permitted\n"
                "2) Why: The handbook permits it.\n"
                "3) What to pay attention to:\n- Verify outputs."
            )))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
        )
        with (
            patch.object(func_OpenAI_query, "get_azure_settings", return_value={
                "api_key": "test-key", "endpoint": "https://example.invalid",
                "api_version": "test", "model_name": "test-model",
            }),
            patch.object(func_OpenAI_query, "AzureOpenAI") as client,
        ):
            client.return_value.chat.completions.create.return_value = response
            answer, token_in, token_out = panel_ai_guidance._answer_ai_case_question(
                "Can I use AI?", "test-model", guidance
            )
            request = client.return_value.chat.completions.create.call_args.kwargs
            messages = request["messages"]
        self.assertIn(guidance, messages[1]["content"])
        self.assertIn(func_OpenAI_query.ANSWER_TEMPLATE, messages[0]["content"])
        self.assertIn("rowspans", messages[0]["content"])
        self.assertEqual(request["max_completion_tokens"], 800)
        self.assertEqual((token_in, token_out), (10, 5))
        full_answer = panel_ai_guidance._append_point_four(answer, principles)
        self.assertIn("1) Permission category:", full_answer)
        self.assertIn("2) Why:", full_answer)
        self.assertIn("3) What to pay attention to:", full_answer)
        self.assertIn("4) AI principles:\n" + principles, full_answer)
        self.assertEqual(panel_ai_guidance._strip_point_four(full_answer), answer)

    def test_existing_point_four_is_replaced_with_current_principles(self):
        _, principles = handbook.load_handbook_guidance()
        answer = "1) Permission category: Permitted\n\n4) AI principles:\nOld principles"
        result = panel_ai_guidance._append_point_four(answer, principles)
        self.assertNotIn("Old principles", result)
        self.assertEqual(result.count("4) AI principles:"), 1)

    def test_submitted_question_uses_handbook_and_displays_all_four_sections(self):
        app = AppTest.from_string(
            "from functions.panel_ai_guidance import render_ai_guidance_panel\n"
            "render_ai_guidance_panel(lambda: '')\n"
        )
        answer = (
            "1) Permission category: Permitted\n"
            "2) Why: Based on the reference.\n"
            "3) What to pay attention to:\n- Verify outputs."
        )
        with (
            patch.object(panel_ai_guidance, "get_ai_guidance_model", return_value="test-model"),
            patch.object(panel_ai_guidance, "query_openai_with_guidance_result", return_value=(answer, 10, 5)) as query,
            patch.object(panel_ai_guidance, "write_to_notion"),
        ):
            app.run()
            app.text_area(key="ai_guidance_query").input("Can I use AI?").run()
            app.button(key="ai_guidance_submit").click().run()
        self.assertFalse(app.exception)
        self.assertIn('id="use-case-reference"', query.call_args.kwargs["guidance_text"])
        rendered = "\n".join(item.value for item in app.markdown)
        for heading in ("Permission category:", "Why:", "What to pay attention to:", "AI principles:"):
            self.assertIn(heading, rendered)
        self.assertIn("Human accountability:", rendered)


class MissingHandbookGuidanceTests(unittest.TestCase):
    def test_missing_handbook_is_reported_as_not_ready(self):
        with patch.object(handbook, "HANDBOOK_PATH", Path("/nonexistent/handbook.html")):
            status = panel_ai_guidance.get_ai_guidance_status()
        self.assertFalse(status["ready"])
        self.assertIn("Could not load handbook guidance", status["message"])

    def test_missing_handbook_does_not_query_model(self):
        app = AppTest.from_string(
            "from functions.panel_ai_guidance import render_ai_guidance_panel\n"
            "render_ai_guidance_panel(lambda: '')\n"
        )
        with (
            patch.object(handbook, "HANDBOOK_PATH", Path("/nonexistent/handbook.html")),
            patch.object(panel_ai_guidance, "get_ai_guidance_model", return_value="test-model"),
            patch.object(panel_ai_guidance, "query_openai_with_guidance_result") as query,
            patch.object(panel_ai_guidance, "write_to_notion"),
        ):
            app.run()
            app.text_area(key="ai_guidance_query").input("Can I use AI?").run()
            app.button(key="ai_guidance_submit").click().run()
        query.assert_not_called()
        self.assertTrue(app.error)


if __name__ == "__main__":
    unittest.main()
