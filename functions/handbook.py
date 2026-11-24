from pathlib import Path
from html.parser import HTMLParser
import re


HANDBOOK_PATH = Path(__file__).resolve().parent.parent / "userhandbook" / "sections-11-5-11-6.html"

_LAST_UPDATE = '<p class="last-update">'
_SECTION_11_5 = '<h1 id="section-11-5">'
_SECTION_11_6 = '<h1 id="section-11-6">'

# Scoped copy of the handbook styles; the handbook's own <style> targets body/h1/table globally.
_STYLE = """<style>
.wgii-handbook {
  container: wgii-handbook / inline-size;
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  color: #17233a;
}
div[data-testid="stMarkdownContainer"]:has(> .wgii-handbook),
div[data-testid="stMarkdown"]:has(.wgii-handbook) { width: 100%; max-width: 100%; min-width: 0; }
.wgii-handbook h1, .wgii-handbook h2, .wgii-handbook h3 { color: #073b70; }
.wgii-handbook .last-update { margin: 0 0 4px; color: #5b6b7c; font-size: 0.9rem; }
.wgii-handbook .note { padding: 12px 16px; border-left: 4px solid #d58a18; background: #fffaf0; }
.wgii-handbook .summary-callout { margin: 20px 0; padding: 16px 20px; border-left: 5px solid #073b70; background: #eef5fb; }
.wgii-handbook .summary-callout h2 { margin: 0 0 8px; }
.wgii-handbook .summary-callout ul { margin: 0; }
.wgii-handbook table { width: 100%; border-collapse: collapse; table-layout: fixed; margin: 18px 0; }
.wgii-handbook th, .wgii-handbook td { padding: 8px 10px; border: 1px solid #b9c7d5; vertical-align: top; background: white; color: #17233a; }
.wgii-handbook th { background: #073b70; color: white; text-align: left; }
.wgii-handbook .author-responsibilities th:first-child,
.wgii-handbook .author-responsibilities td:first-child { width: 16%; }
.wgii-handbook #use-case-reference { min-width: 0; font-size: 14px; }
.wgii-handbook #use-case-reference th,
.wgii-handbook #use-case-reference td { padding: 6px 8px; overflow-wrap: break-word; hyphens: auto; }
.wgii-handbook #use-case-reference th:nth-child(1) { width: 16%; }
.wgii-handbook #use-case-reference th:nth-child(2) { width: 30%; }
.wgii-handbook #use-case-reference th:nth-child(3) { width: 6.5em; white-space: nowrap; text-align: center; }
.wgii-handbook #use-case-reference th:nth-child(4) { width: auto; }
.wgii-handbook #use-case-reference .attention ol { padding-left: 1.3em; }
@container wgii-handbook (max-width: 900px) {
  .wgii-handbook #use-case-reference { font-size: 13px; }
  .wgii-handbook #use-case-reference th:nth-child(3) { width: 5.8em; }
}
@container wgii-handbook (max-width: 620px) {
  .wgii-handbook #use-case-reference { min-width: 600px; font-size: 12px; }
}
.wgii-handbook .legend { display: flex; flex-wrap: wrap; gap: 12px 34px; margin: 8px 0 16px; }
.wgii-handbook .legend span { display: flex; align-items: center; gap: 8px; }
.wgii-handbook .check, .wgii-handbook .cross { font-size: 24px; line-height: 1; }
.wgii-handbook .check, .wgii-handbook .permission.green { color: #16834a; }
.wgii-handbook .cross, .wgii-handbook .permission.red { color: #d7193f; }
.wgii-handbook .cat-cell { background: #eef5fb; color: #073b70; font-weight: 700; }
.wgii-handbook .permission { text-align: center; font-weight: 700; }
.wgii-handbook .attention { background: #fffaf0; }
.wgii-handbook .attention ol { margin: 0; padding-left: 24px; }
.wgii-handbook .principles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 16px; }
.wgii-handbook .principles-title { grid-column: 1 / -1; padding: 14px; background: #073b70; color: white; font-weight: 700; }
.wgii-handbook .principle { min-width: 0; padding: 11px 12px; border-radius: 7px; background: #eaf3fb; overflow-wrap: anywhere; }
.wgii-handbook .principle h3 { margin: 0 0 5px; font-size: 1.1rem; }
.wgii-handbook .pnum { margin-right: 5px; }
@container wgii-handbook (max-width: 480px) {
  .wgii-handbook .principles { gap: 4px; }
  .wgii-handbook .principle { padding: 6px; font-size: 0.8rem; }
  .wgii-handbook .principle h3 { font-size: 0.9rem; }
}
</style>"""


def _section_start(text: str, heading: str) -> int:
    """Start at the "Last update" line directly above the heading, if present."""
    heading_index = text.index(heading)
    update_index = text.rfind(_LAST_UPDATE, 0, heading_index)
    if update_index != -1 and text[update_index:heading_index].count("<p") == 1:
        return update_index
    return heading_index


def _section_body(section: str, text: str) -> str:
    if section == "11.5":
        start = _section_start(text, _SECTION_11_5)
        end = _section_start(text, _SECTION_11_6)
    elif section == "11.6":
        start = _section_start(text, _SECTION_11_6)
        end = text.index("</main>", start)
    else:
        raise ValueError(f"Unknown handbook section: {section}")

    return text[start:end].strip()


def load_handbook_section(section: str) -> str:
    """Return section "11.5" or "11.6" of the handbook as scoped HTML for st.markdown."""
    body = _section_body(section, HANDBOOK_PATH.read_text(encoding="utf-8"))
    # Blank lines would end Streamlit's raw HTML block and render the rest as Markdown.
    html = f'{_STYLE}\n<section class="wgii-handbook">\n{body}\n</section>'
    return "\n".join(line for line in html.splitlines() if line.strip())


class _PrinciplesParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_list = False
        self.finished = False
        self.in_item = False
        self.item: list[str] = []
        self.items: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "ul" and not self.finished:
            self.in_list = True
        elif tag == "li" and self.in_list:
            self.in_item = True
            self.item = []

    def handle_data(self, data: str) -> None:
        if self.in_item:
            self.item.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "li" and self.in_item:
            self.items.append(" ".join("".join(self.item).split()))
            self.in_item = False
        elif tag == "ul" and self.in_list:
            self.in_list = False
            self.finished = True


def load_handbook_guidance() -> tuple[str, str]:
    """Load current guidance and the four principles for the checker."""
    text = HANDBOOK_PATH.read_text(encoding="utf-8")
    principles_section = _section_body("11.5", text)
    reference_section = _section_body("11.6", text)
    parser = _PrinciplesParser()
    parser.feed(principles_section)
    labels = ("Human accountability:", "Transparency and traceability:",
              "Confidentiality and data protection:", "Comprehensiveness:")
    if len(parser.items) != 4 or any(
        not item.startswith(label) for item, label in zip(parser.items, labels)
    ):
        raise ValueError("Could not find the four AI principles in handbook section 11.5.")
    guidance = re.sub(r"<!--.*?-->", "", f"{principles_section}\n{reference_section}", flags=re.DOTALL)
    if 'id="use-case-reference"' not in guidance:
        raise ValueError("Could not find the AI use case reference in handbook section 11.6.")
    principles = "\n".join(
        f"- **{label}**{item[len(label):]}"
        for item, label in zip(parser.items, labels)
    )
    return guidance, principles
