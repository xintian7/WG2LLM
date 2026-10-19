import unittest
from types import SimpleNamespace
from unittest.mock import patch

from openai import NOT_GIVEN
from streamlit.testing.v1 import AppTest

from functions import env_loader, panel_grammar


GRAMMAR_APP = (
    "from functions.panel_grammar import render_grammar_panel\n"
    "render_grammar_panel(lambda: '')\n"
)


def _response(text: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )


class GrammarModelTests(unittest.TestCase):
    def setUp(self):
        self.settings = {
            "endpoint": "https://existing-resource.openai.azure.com/",
            "api_version": "2024-10-21",
            "api_key": "test-key",
        }
        settings_patch = patch.object(
            env_loader, "get_azure_settings", return_value=self.settings
        )
        client_patch = patch.object(panel_grammar, "AzureOpenAI")
        settings_patch.start()
        self.addCleanup(settings_patch.stop)
        self.client_factory = client_patch.start()
        self.addCleanup(client_patch.stop)
        self.create = self.client_factory.return_value.chat.completions.create

    def test_sol_is_default_and_gpt_41_models_are_removed(self):
        for configured, expected in (
            (("gpt-4.1-mini", "gpt-5.4"), ["gpt-6.1-sol", "gpt-5.4"]),
            (("gpt-5.4", "gpt-6.1-sol"), ["gpt-6.1-sol", "gpt-5.4"]),
            (("gpt-6.1-sol", "gpt-5.4"), ["gpt-6.1-sol", "gpt-5.4"]),
            (("gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"), ["gpt-6.1-sol"]),
            (("gpt-4.1-2025-04-14",), ["gpt-6.1-sol"]),
        ):
            with (
                self.subTest(configured=configured),
                patch.object(
                    env_loader, "get_azure_model_options", return_value=configured
                ),
            ):
                app = AppTest.from_string(GRAMMAR_APP).run()
                self.assertFalse(app.exception)
                selector = app.selectbox(key="grammar_model")
                self.assertEqual(
                    selector.options,
                    [
                        f"{model} (with Data and Information Protection under GDPR and ISO27001)"
                        for model in expected
                    ],
                )
                self.assertEqual(selector.value, "gpt-6.1-sol")

    def test_saved_selection_resets_only_when_no_longer_available(self):
        for selected in ("gpt-4.1", "gpt-4.1-mini", "gpt-5.4", "gpt-6.1-sol"):
            with (
                self.subTest(selected=selected),
                patch.object(
                    env_loader,
                    "get_azure_model_options",
                    return_value=("gpt-4.1-mini", "gpt-5.4"),
                ),
            ):
                app = AppTest.from_string(GRAMMAR_APP)
                app.session_state["grammar_model"] = selected
                app.run()
                self.assertFalse(app.exception)
                expected = selected if selected in ("gpt-5.4", "gpt-6.1-sol") else "gpt-6.1-sol"
                self.assertEqual(app.selectbox(key="grammar_model").value, expected)
                app.selectbox(key="grammar_model").select("gpt-5.4").run()
                self.assertFalse(app.exception)
                self.assertEqual(app.selectbox(key="grammar_model").value, "gpt-5.4")

    def test_sol_uses_supplied_connection_and_deployment(self):
        self.create.return_value = _response("Corrected text.")

        result = panel_grammar._correct_grammar_with_ai("Original text.", "gpt-6.1-sol")

        self.assertEqual(result, (True, "Corrected text.", 10, 5))
        self.client_factory.assert_called_once_with(
            api_version="2024-12-01-preview",
            azure_endpoint="https://azureopenaitsu.openai.azure.com/",
            api_key="test-key",
        )
        kwargs = self.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "gpt-6.1-sol")
        self.assertEqual(kwargs["max_completion_tokens"], 3000)
        for parameter in (
            "temperature", "top_p", "frequency_penalty", "presence_penalty"
        ):
            self.assertIs(kwargs[parameter], NOT_GIVEN)
        self.assertEqual(self.settings["api_version"], "2024-10-21")

    def test_existing_model_connection_and_parameters_are_unchanged(self):
        self.create.return_value = _response("Corrected text.")

        result = panel_grammar._correct_grammar_with_ai("Original text.", "gpt-5.4")

        self.assertEqual(result, (True, "Corrected text.", 10, 5))
        self.client_factory.assert_called_once_with(
            api_version=self.settings["api_version"],
            azure_endpoint=self.settings["endpoint"],
            api_key="test-key",
        )
        kwargs = self.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "gpt-5.4")
        self.assertEqual(kwargs["temperature"], 0)
        self.assertEqual(kwargs["top_p"], 1.0)
        self.assertEqual(kwargs["frequency_penalty"], 0.0)
        self.assertEqual(kwargs["presence_penalty"], 0.0)

    def test_non_english_response_preserves_validation_and_token_usage(self):
        self.create.return_value = _response("__NON_ENGLISH__")

        result = panel_grammar._correct_grammar_with_ai("Bonjour.", "gpt-6.1-sol")

        self.assertEqual(result, (False, "Please input English text only.", 10, 5))


if __name__ == "__main__":
    unittest.main()
