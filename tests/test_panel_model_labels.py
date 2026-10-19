import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from functions import env_loader, panel_ai_guidance


class ModelLabelTests(unittest.TestCase):
    def test_first_three_panels_display_notice_but_keep_raw_model_values(self):
        with (
            patch.object(
                env_loader,
                "get_azure_model_options",
                return_value=("gpt-4.1-mini", "gpt-5.4"),
            ),
            patch.object(
                panel_ai_guidance, "get_ai_guidance_model", return_value="gpt-5.4"
            ),
            patch.object(
                panel_ai_guidance,
                "get_ai_guidance_status",
                return_value={"ready": False, "message": "Test knowledge base."},
            ),
        ):
            for module, renderer, key, models in (
                (
                    "panel_ai_guidance",
                    "render_ai_guidance_panel",
                    "ai_guidance_model",
                    ["gpt-5.4"],
                ),
                (
                    "panel_rephrase",
                    "render_rephrase_panel",
                    "rephrase_model",
                    ["gpt-6.1-sol", "gpt-5.4"],
                ),
                (
                    "panel_grammar",
                    "render_grammar_panel",
                    "grammar_model",
                    ["gpt-6.1-sol", "gpt-5.4"],
                ),
            ):
                with self.subTest(panel=module):
                    app = AppTest.from_string(
                        f"from functions.{module} import {renderer}\n"
                        f"{renderer}(lambda: '')\n"
                    ).run()
                    self.assertFalse(app.exception)
                    selector = app.selectbox(key=key)
                    self.assertEqual(
                        selector.options,
                        [
                            f"{model} (with Data and Information Protection under GDPR and ISO27001)"
                            for model in models
                        ],
                    )
                    self.assertEqual(selector.value, models[0])
                    self.assertEqual(app.session_state[key], models[0])

                    selector.select(models[-1]).run()
                    self.assertFalse(app.exception)
                    self.assertEqual(app.selectbox(key=key).value, models[-1])
                    self.assertEqual(app.session_state[key], models[-1])


if __name__ == "__main__":
    unittest.main()
