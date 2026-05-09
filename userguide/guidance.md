# Guidance

This document introduces **WGII AI Assistant (version 0.1c)**, designed to support IPCC AR7 authors using AI-enhanced workflows.

## 1) What this app does

The WGII AI Assistant helps users:

- check whether a proposed AI use case is aligned with WGII AI guidance,
- rephrase English text into formal scientific writing style,
- correct English grammar with highlighted edits,
- report new AI use cases to WGII TSU,
- view a reference figure for AI use cases,
- access Terms of Use and Privacy Policy,
- submit feedback to WGII TSU.

The app does not replace author judgment, chapter leadership decisions, or IPCC governance procedures.

## 2) Quick start

### Prerequisites

- web browser,
- internet access,
- valid Azure OpenAI settings configured by the TSU or deployment environment.

### Web app

Use the deployed WGII AI Assistant URL provided by WGII TSU.

## 3) Core controls

### Check AI use cases

- Enter a question such as: "Can I use AI to rephrase assessment text?"
- Click **Submit** to receive a guidance-based answer.
- Output is grounded in the guidance content bundled with the app.

![alt text](image.png)

### View AI use case reference

- Opens the AI use case reference figure.
- You can view and download the image.
- You can also expand the figure to a full size by clicking the button on the top left. 
![alt text](image-1.png)

### Rephrase sentences

- Input English text (up to 300 words).
- Click **Rephrase text** to receive a refined version in formal academic style.
- Review the output in **Rephrased text** and use **Copy text** when needed.
- Optional: enable the checkbox to share prompts/results with TSU for app improvement.
- Important: authors are responsible for verifying and proofreading LLM-rephrased text before including it in the AR7 report.

### Check grammar

- Input English text (up to 3000 words).
- Click **Correct grammar** to generate corrected text.
- Review results in two tabs:
	- **Corrected text** (clean corrected output),
	- **Highlighted changes** (edits marked in context).
- Optional: enable the checkbox to share prompts/results with TSU for app improvement.

### Report a new AI use case

- Open **Report a new AI use case** from the main buttons.
- Submit examples of new or unclear AI use cases that should be considered for future guidance updates.
- Add contact information if you want WGII TSU to follow up.

### Use case scenario analysis

- This feature is still under development and will be available in a future release.

### Give feedback

- Open **Give feedback** from the sidebar to access the dedicated feedback page.
- Share questions, issues, or suggestions using the feedback form.
- Feedback is submitted to the TSU feedback database for app improvement.

## 4) How responses are framed

For permission-check style prompts, the app returns:

1. Permission category.
2. Why (brief reason from guidance).
3. What to pay attention to (conditions, cautions, and limits).

If a question is outside the guidance scope, the app indicates that directly.

## 5) Recommended workflow

1. Draft your AI-use question in practical terms (task, context, expected output).
2. Run **Check AI use cases**.
3. Review the permission category and cautions.
4. If needed, refine your question and re-run.
5. Align your final action with WGII procedures and leadership direction.

## 6) Troubleshooting

- **No response from model**: verify endpoint, API key, deployment, and API version.
- **Unexpected answer quality**: ask a more specific question and include intended use context.
- **English-only error**: rephrase and grammar tools accept English input only.
- **Input too long**: reduce text to tool limits (300 words for rephrase, 3000 words for grammar).

## 7) Notes

- This assistant is a support tool, not a policy authority.
- Guidance and app behavior may be updated over time.
- The tool is based on Azure OpenAI studio.
- For questions or suggestions, contact WGII TSU.