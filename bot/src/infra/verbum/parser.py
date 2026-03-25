import logging
import re
from html.parser import HTMLParser

from src.infra.schemas.verbum import ParsedCard, ParsedDefinition

logger = logging.getLogger(__name__)


class _ArticleHTMLParser(HTMLParser):
    """State-machine HTML parser for tsblm2022 dictionary articles."""

    def __init__(self) -> None:
        super().__init__()
        self.headword = ""
        self.headword_with_accent = ""
        self.part_of_speech: str | None = None
        self.definitions: list[ParsedDefinition] = []
        self.phrases: list[str] = []

        self._in_hw = False
        self._in_hw_alt = False
        self._in_accent = False
        self._in_example = False
        self._in_phrase = False
        self._in_abbr = False
        self._in_table = 0
        self._in_def_number = False

        self._current_abbr_title: str | None = None
        self._current_def: ParsedDefinition | None = None
        self._example_buf: list[str] = []
        self._phrase_buf: list[str] = []
        self._pos_candidates: list[str] = []
        self._saw_first_def = False
        self._headword_done = False
        self._in_first_p = True  # first <p> is grammar line, skip body text
        self._p_depth = 0
        self._current_p_class = ""
        self._hit_separator = False  # stop at || separator

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._in_table += 1
            return
        if self._in_table:
            return

        attr_dict = dict(attrs)
        cls = attr_dict.get("class") or ""

        if tag == "p":
            self._p_depth += 1
            self._current_p_class = cls
            if self._headword_done and self._in_first_p:
                # We're still in the first <p> (grammar line) after headword
                pass

        if tag == "strong" and "hw-alt" in cls:
            self._in_hw_alt = True
        elif tag == "strong" and "hw" in cls:
            self._in_hw = True
        elif tag == "strong" and "phr" in cls:
            self._in_phrase = True
            self._phrase_buf = []
        elif (
            tag == "strong"
            and not self._in_hw
            and not self._in_hw_alt
            and not self._in_phrase
        ):
            self._in_def_number = True
        elif tag == "span" and "accent" in cls:
            self._in_accent = True
        elif tag == "v-ex":
            self._in_example = True
            self._example_buf = []
        elif tag == "v-abbr":
            self._in_abbr = True
            self._current_abbr_title = attr_dict.get("data-bs-title")

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            self._in_table = max(0, self._in_table - 1)
            return
        if self._in_table:
            return

        if tag == "p":
            self._p_depth = max(0, self._p_depth - 1)
            if self._headword_done and self._in_first_p and self._p_depth == 0:
                self._in_first_p = False

        if tag == "strong":
            if self._in_hw:
                self._in_hw = False
                self._headword_done = True
            elif self._in_hw_alt:
                self._in_hw_alt = False
            elif self._in_phrase:
                self._in_phrase = False
                phrase_text = "".join(self._phrase_buf).strip()
                if phrase_text:
                    self.phrases.append(phrase_text)
                self._phrase_buf = []
            elif self._in_def_number:
                self._in_def_number = False
        elif tag == "span" and self._in_accent:
            self._in_accent = False
        elif tag == "v-ex":
            self._in_example = False
            example_text = "".join(self._example_buf).strip()
            if example_text and self._current_def is not None:
                self._current_def.examples.append(example_text)
            self._example_buf = []
        elif tag == "v-abbr":
            self._in_abbr = False
            self._current_abbr_title = None

    def handle_data(self, data: str) -> None:
        if self._in_table or self._hit_separator:
            return

        # Headword
        if self._in_hw:
            self.headword += data
            self.headword_with_accent += data
            return

        # Skip hw-alt
        if self._in_hw_alt:
            return

        text = data.strip()
        if not text:
            return

        # Check for || separator — stop collecting after it
        if "||" in text:
            self._hit_separator = True
            return

        # Examples
        if self._in_example:
            self._example_buf.append(data)
            return

        # Phrases
        if self._in_phrase:
            self._phrase_buf.append(data)
            return

        # Abbreviations — collect POS candidates from first <p>
        if self._in_abbr and self._current_abbr_title and not self._saw_first_def:
            self._pos_candidates.append(self._current_abbr_title)
            return

        if self._in_abbr:
            return

        # Skip grammar line (first <p> after headword)
        if self._in_first_p:
            return

        # Definition numbers
        if self._in_def_number:
            match = re.match(r"(\d+)\.", text)
            if match:
                num = int(match.group(1))
                self._saw_first_def = True
                self._current_def = ParsedDefinition(number=num, text="")
                self.definitions.append(self._current_def)
            return

        # Body text — definition content
        if self._headword_done:
            if self._current_def is not None:
                if self._current_def.text:
                    self._current_def.text += " " + text
                else:
                    self._current_def.text = text
            elif "ms-" in self._current_p_class:
                # Text in indented paragraph without a numbered def — single definition
                if not self._saw_first_def:
                    self._current_def = ParsedDefinition(text=text)
                    self.definitions.append(self._current_def)

    def finalize(self) -> None:
        self.headword = self.headword.strip()
        self.headword_with_accent = self.headword_with_accent.strip()

        # Clean accent marks from plain headword for display
        self.headword = self.headword.replace("\u0301", "")

        # Determine part of speech
        pos_keywords = [
            "мужчынскі род",
            "жаночы род",
            "ніякі род",
            "назоўнік",
            "прыметнік",
            "дзеяслоў",
            "прыслоўе",
            "зборны назоўнік",
        ]
        for candidate in self._pos_candidates:
            for kw in pos_keywords:
                if kw in candidate:
                    self.part_of_speech = candidate
                    return


class VerbumParser:
    def parse_article(self, html_content: str, dictionary_id: str) -> ParsedCard:
        try:
            parser = _ArticleHTMLParser()
            parser.feed(html_content)
            parser.finalize()

            definitions = parser.definitions
            if not definitions:
                plain_text = self._strip_html(html_content)
                hw = parser.headword
                if hw and plain_text.startswith(hw):
                    plain_text = plain_text[len(hw) :].strip(" ,.-")
                if plain_text:
                    definitions = [ParsedDefinition(text=plain_text)]

            for d in definitions:
                d.text = re.sub(r"\s+", " ", d.text).strip(" ,.")

            accent: str | None = parser.headword_with_accent
            if accent == parser.headword or not accent:
                accent = None

            return ParsedCard(
                headword=parser.headword or self._extract_headword(html_content),
                accent=accent,
                part_of_speech=parser.part_of_speech,
                definitions=definitions,
                phrases=parser.phrases,
                raw_html=html_content,
                dictionary_id=dictionary_id,
            )
        except Exception:
            logger.exception("Failed to parse article HTML, falling back to raw text")
            return self._fallback_parse(html_content, dictionary_id)

    def _strip_html(self, html: str) -> str:
        clean = re.sub(r"<[^>]+>", " ", html)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def _extract_headword(self, html: str) -> str:
        match = re.search(r'class="hw"[^>]*>([^<]+)', html)
        if match:
            return match.group(1).strip()
        return ""

    def _fallback_parse(self, html: str, dictionary_id: str) -> ParsedCard:
        headword = self._extract_headword(html)
        plain = self._strip_html(html)
        return ParsedCard(
            headword=headword,
            definitions=[ParsedDefinition(text=plain)] if plain else [],
            raw_html=html,
            dictionary_id=dictionary_id,
        )


def format_card_for_telegram(card: ParsedCard) -> str:
    parts: list[str] = []

    header = f"<b>{_escape(card.headword)}</b>"
    if card.accent:
        header += f"  ({_escape(card.accent)})"
    parts.append(header)

    if card.part_of_speech:
        parts.append(f"<i>{_escape(card.part_of_speech)}</i>")

    parts.append("")

    for d in card.definitions:
        prefix = f"<b>{d.number}.</b> " if d.number else ""
        parts.append(f"{prefix}{_escape(d.text)}")
        for ex in d.examples:
            parts.append(f"    <i>{_escape(ex)}</i>")

    if card.phrases:
        parts.append("")
        for phrase in card.phrases:
            parts.append(f"  <b>{_escape(phrase)}</b>")

    result = "\n".join(parts)

    if len(result) > 4000:
        result = result[:4000] + "\n..."

    return result


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
