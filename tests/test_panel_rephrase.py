import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from openai import NOT_GIVEN

from functions import env_loader, panel_rephrase


def _response(text: str, input_tokens: int = 10, output_tokens: int = 5):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
        usage=SimpleNamespace(
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
        ),
    )


class RephraseModelTests(unittest.TestCase):
    def setUp(self):
        self.settings = {
            "endpoint": "https://existing-resource.openai.azure.com/",
            "api_version": "2024-10-21",
            "api_key": "test-key",
        }
        settings_patch = patch.object(
            env_loader, "get_azure_settings", return_value=self.settings
        )
        client_patch = patch.object(panel_rephrase, "AzureOpenAI")
        settings_patch.start()
        self.addCleanup(settings_patch.stop)
        self.client_factory = client_patch.start()
        self.addCleanup(client_patch.stop)
        self.create = self.client_factory.return_value.chat.completions.create

    def test_sol_is_default_and_gpt_41_models_are_removed(self):
        for configured, expected in (
            (("existing-model",), ("gpt-6.1-sol", "existing-model")),
            (("existing-model", "gpt-6.1-sol"), ("gpt-6.1-sol", "existing-model")),
            (("gpt-6.1-sol", "existing-model"), ("gpt-6.1-sol", "existing-model")),
            (("gpt-4.1-mini", "gpt-5.4"), ("gpt-6.1-sol", "gpt-5.4")),
            (("gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"), ("gpt-6.1-sol",)),
            (("gpt-4.1-2025-04-14", "gpt-6.1-sol"), ("gpt-6.1-sol",)),
        ):
            with self.subTest(configured=configured):
                mock_st = MagicMock()
                mock_st.session_state = {}
                mock_st.text_area.return_value = ""
                mock_st.button.return_value = False
                with (
                    patch.object(panel_rephrase, "st", mock_st),
                    patch.object(panel_rephrase.components, "html"),
                    patch.object(
                        env_loader,
                        "get_azure_model_options",
                        return_value=configured,
                    ),
                ):
                    panel_rephrase.render_rephrase_panel(lambda: "")

                kwargs = mock_st.selectbox.call_args.kwargs
                options = kwargs["options"]
                self.assertEqual(options, expected)
                self.assertEqual(options[kwargs["index"]], "gpt-6.1-sol")

    def test_saved_selection_resets_only_when_no_longer_available(self):
        for selected in ("gpt-4.1", "gpt-4.1-mini", "gpt-5.4", "gpt-6.1-sol"):
            with self.subTest(selected=selected):
                mock_st = MagicMock()
                mock_st.session_state = {"rephrase_model": selected}
                mock_st.text_area.return_value = ""
                mock_st.button.return_value = False
                with (
                    patch.object(panel_rephrase, "st", mock_st),
                    patch.object(panel_rephrase.components, "html"),
                    patch.object(
                        env_loader,
                        "get_azure_model_options",
                        return_value=("gpt-4.1-mini", "gpt-5.4"),
                    ),
                ):
                    panel_rephrase.render_rephrase_panel(lambda: "")

                expected = selected if selected in ("gpt-5.4", "gpt-6.1-sol") else "gpt-6.1-sol"
                self.assertEqual(mock_st.session_state["rephrase_model"], expected)

    def test_sol_uses_supplied_connection_and_deployment(self):
        self.create.return_value = _response("Rephrased text.")

        result = panel_rephrase._rephrase_with_ai("Original text.", "gpt-6.1-sol")

        self.assertEqual(result, (True, "Rephrased text.", 10, 5))
        self.client_factory.assert_called_once_with(
            api_version="2024-12-01-preview",
            azure_endpoint="https://azureopenaitsu.openai.azure.com/",
            api_key="test-key",
        )
        kwargs = self.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "gpt-6.1-sol")
        self.assertEqual(kwargs["max_completion_tokens"], 1200)
        for parameter in (
            "temperature", "top_p", "frequency_penalty", "presence_penalty"
        ):
            self.assertIs(kwargs[parameter], NOT_GIVEN)

    def test_sol_retry_preserves_deployment_and_token_accounting(self):
        self.create.side_effect = [
            _response("- First point\n- Second point"),
            _response("One continuous paragraph.", 20, 8),
        ]

        result = panel_rephrase._rephrase_with_ai("Original text.", "gpt-6.1-sol")

        self.assertEqual(result, (True, "One continuous paragraph.", 30, 13))
        self.assertEqual(self.create.call_count, 2)
        for call in self.create.call_args_list:
            self.assertEqual(call.kwargs["model"], "gpt-6.1-sol")
            for parameter in (
                "temperature", "top_p", "frequency_penalty", "presence_penalty"
            ):
                self.assertIs(call.kwargs[parameter], NOT_GIVEN)
        self.assertIn(
            "one paragraph only",
            self.create.call_args.kwargs["messages"][1]["content"],
        )

    def test_existing_model_connection_and_parameters_are_unchanged(self):
        self.create.side_effect = [
            _response("- First point\n- Second point"),
            _response("Rephrased text."),
        ]

        result = panel_rephrase._rephrase_with_ai("Original text.", "existing-model")

        self.assertEqual(result, (True, "Rephrased text.", 20, 10))
        self.client_factory.assert_called_once_with(
            api_version=self.settings["api_version"],
            azure_endpoint=self.settings["endpoint"],
            api_key="test-key",
        )
        self.assertEqual(self.create.call_count, 2)
        for call in self.create.call_args_list:
            kwargs = call.kwargs
            self.assertEqual(kwargs["model"], "existing-model")
            self.assertEqual(kwargs["temperature"], 0)
            self.assertEqual(kwargs["top_p"], 1.0)
            self.assertEqual(kwargs["frequency_penalty"], 0.0)
            self.assertEqual(kwargs["presence_penalty"], 0.0)


if __name__ == "__main__":
    unittest.main()
