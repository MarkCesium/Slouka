from src.infra.verbum.parser import (
    VerbumParser,
    _ExplanatoryParser,
    _KlyshkaParser,
    _normalize_ws,
    _Rbs10Parser,
    _strip_accent,
)


class TestStripAccent:
    def test_removes_combining_acute(self) -> None:
        assert _strip_accent("сло\u0301ва") == "слова"

    def test_preserves_other_chars(self) -> None:
        assert _strip_accent("привет") == "привет"

    def test_multiple_accents(self) -> None:
        assert _strip_accent("ма\u0301ці\u0301") == "маці"


class TestNormalizeWs:
    def test_collapses_spaces(self) -> None:
        assert _normalize_ws("a  b   c") == "a b c"

    def test_collapses_newlines(self) -> None:
        assert _normalize_ws("a\n\nb") == "a b"


class TestExplanatoryParser:
    def _parse(self, html: str) -> _ExplanatoryParser:
        p = _ExplanatoryParser()
        p.feed(html)
        p.finalize()
        return p

    def test_headword_extraction(self) -> None:
        html = '<p><strong class="hw">слова</strong></p>'
        p = self._parse(html)
        assert p.headword == "слова"

    def test_headword_with_accent(self) -> None:
        html = '<p><strong class="hw">сло\u0301ва</strong></p>'
        p = self._parse(html)
        assert p.headword == "слова"
        assert p.headword_with_accent == "сло\u0301ва"

    def test_headword_with_accent_span(self) -> None:
        html = '<p><strong class="hw">сло<span class="accent">\u0301</span>ва</strong></p>'
        p = self._parse(html)
        assert p.headword == "слова"
        assert "сло" in p.headword_with_accent
        assert "ва" in p.headword_with_accent

    def test_numbered_definitions(self) -> None:
        html = """
        <p><strong class="hw">слова</strong></p>
        <p>граматыка</p>
        <p class="ms-3"><strong>1.</strong> першае значэнне</p>
        <p class="ms-3"><strong>2.</strong> другое значэнне</p>
        """
        p = self._parse(html)
        assert len(p.definitions) == 2
        assert p.definitions[0].number == 1
        assert "першае значэнне" in p.definitions[0].text
        assert p.definitions[1].number == 2
        assert "другое значэнне" in p.definitions[1].text

    def test_unnumbered_definition(self) -> None:
        html = """
        <p><strong class="hw">слова</strong></p>
        <p>граматыка</p>
        <p class="ms-3">адзінае значэнне</p>
        """
        p = self._parse(html)
        assert len(p.definitions) == 1
        assert p.definitions[0].number is None
        assert "адзінае значэнне" in p.definitions[0].text

    def test_examples(self) -> None:
        html = """
        <p><strong class="hw">слова</strong></p>
        <p>граматыка</p>
        <p class="ms-3"><strong>1.</strong> значэнне <v-ex>прыклад</v-ex></p>
        """
        p = self._parse(html)
        assert len(p.definitions) == 1
        assert len(p.definitions[0].examples) == 1
        assert "прыклад" in p.definitions[0].examples[0]

    def test_table_skipped(self) -> None:
        html = """
        <p><strong class="hw">слова</strong></p>
        <p>граматыка</p>
        <table><tr><td>grammar data</td></tr></table>
        <p class="ms-3"><strong>1.</strong> значэнне</p>
        """
        p = self._parse(html)
        assert len(p.definitions) == 1
        assert "grammar data" not in p.definitions[0].text

    def test_separator_stops_parsing(self) -> None:
        html = """
        <p><strong class="hw">слова</strong></p>
        <p>граматыка</p>
        <p class="ms-3"><strong>1.</strong> першае</p>
        <p>||</p>
        <p class="ms-3"><strong>2.</strong> другое</p>
        """
        p = self._parse(html)
        assert len(p.definitions) == 1
        assert p.definitions[0].number == 1

    def test_hw_alt_skipped(self) -> None:
        html = """
        <p><strong class="hw">слова</strong> <strong class="hw-alt">жаночая форма</strong></p>
        <p>граматыка</p>
        <p class="ms-3">значэнне</p>
        """
        p = self._parse(html)
        assert p.headword == "слова"
        assert "жаночая" not in p.headword

    def test_pos_detection(self) -> None:
        html = """
        <p><strong class="hw">слова</strong>
        <v-abbr data-bs-title="мужчынскі род">м.</v-abbr></p>
        <p class="ms-3">значэнне</p>
        """
        p = self._parse(html)
        assert p.part_of_speech is not None
        assert "мужчынскі род" in p.part_of_speech

    def test_phrase_extraction(self) -> None:
        html = """
        <p><strong class="hw">слова</strong></p>
        <p>граматыка</p>
        <p class="ms-3"><strong>1.</strong> значэнне</p>
        <p><strong class="phr">фраза тэсту</strong></p>
        """
        p = self._parse(html)
        assert len(p.phrases) >= 1
        assert "фраза тэсту" in p.phrases[0]


class TestKlyshkaParser:
    def _parse(self, html: str) -> _KlyshkaParser:
        p = _KlyshkaParser()
        p.feed(html)
        p.finalize()
        return p

    def test_synonym_extraction(self) -> None:
        html = '<p><strong class="hw">слова</strong>, сінонім1, сінонім2</p>'
        p = self._parse(html)
        assert p.headword == "слова"
        assert "сінонім1" in p.body_text
        assert "сінонім2" in p.body_text

    def test_empty_body(self) -> None:
        html = '<p><strong class="hw">слова</strong></p>'
        p = self._parse(html)
        assert p.headword == "слова"
        assert p.body_text.strip() == ""

    def test_accent_in_headword(self) -> None:
        html = '<p><strong class="hw">сло\u0301ва</strong>, сінонім</p>'
        p = self._parse(html)
        assert p.headword == "слова"
        assert p.headword_with_accent == "сло\u0301ва"


class TestRbs10Parser:
    def _parse(self, html: str) -> _Rbs10Parser:
        p = _Rbs10Parser()
        p.feed(html)
        p.finalize()
        return p

    def test_headword_extraction(self) -> None:
        html = '<p><b class="hw">слово</b></p><p>пераклад</p>'
        p = self._parse(html)
        assert p.headword == "слово"

    def test_accent_span_reassembly(self) -> None:
        html = '<p><b class="hw">хлап<span class="accent">е\u0301</span>ц</b></p><p>хлопец</p>'
        p = self._parse(html)
        assert p.headword == "хлапец"
        assert "е\u0301" in p.headword_with_accent or "е́" in p.headword_with_accent

    def test_numbered_definitions(self) -> None:
        html = """
        <p><b class="hw">слово</b></p>
        <p><b>1.</b> першы пераклад</p>
        <p><b>2.</b> другі пераклад</p>
        """
        p = self._parse(html)
        assert len(p.definitions) == 2
        assert p.definitions[0].number == 1
        assert p.definitions[1].number == 2

    def test_phrase_marker(self) -> None:
        html = """
        <p><b class="hw">слово</b></p>
        <p><b>1.</b> пераклад</p>
        <p>◊</p>
        <p class="ms-3"><b>фраза</b> тэкст</p>
        """
        p = self._parse(html)
        assert len(p.definitions) == 1
        assert len(p.phrases) >= 1

    def test_pos_detection_russian(self) -> None:
        html = """
        <p><b class="hw">слово</b>
        <v-abbr data-bs-title="мужской род">м.</v-abbr></p>
        <p>пераклад</p>
        """
        p = self._parse(html)
        assert p.part_of_speech is not None
        assert "мужской род" in p.part_of_speech


class TestVerbumParserDispatcher:
    def setup_method(self) -> None:
        self.parser = VerbumParser()

    def test_routes_to_explanatory(self) -> None:
        html = '<p><strong class="hw">тэст</strong></p><p>грам</p><p class="ms-3">значэнне</p>'
        card = self.parser.parse_article(html, "tsblm2022")
        assert card.headword == "тэст"
        assert card.dictionary_id == "tsblm2022"

    def test_routes_to_klyshka(self) -> None:
        html = '<p><strong class="hw">тэст</strong>, сінонім</p>'
        card = self.parser.parse_article(html, "klyshka")
        assert card.headword == "тэст"
        assert card.dictionary_id == "klyshka"

    def test_routes_to_rbs10(self) -> None:
        html = '<p><b class="hw">тест</b></p><p>тэст</p>'
        card = self.parser.parse_article(html, "rbs10")
        assert card.headword == "тест"
        assert card.dictionary_id == "rbs10"

    def test_accent_none_when_no_accent(self) -> None:
        html = '<p><strong class="hw">тэст</strong></p><p>грам</p><p class="ms-3">значэнне</p>'
        card = self.parser.parse_article(html, "tsblm2022")
        assert card.accent is None

    def test_accent_set_when_present(self) -> None:
        html = (
            '<p><strong class="hw">тэ\u0301ст</strong></p><p>грам</p><p class="ms-3">значэнне</p>'
        )
        card = self.parser.parse_article(html, "tsblm2022")
        assert card.accent is not None
        assert "\u0301" in card.accent

    def test_fallback_on_empty_definitions(self) -> None:
        html = '<p><strong class="hw">тэст</strong></p>'
        card = self.parser.parse_article(html, "tsblm2022")
        # Should have at least a fallback definition from stripped HTML
        assert card.headword == "тэст"

    def test_dictionary_name_set(self) -> None:
        html = '<p><strong class="hw">тэст</strong></p><p>грам</p><p class="ms-3">значэнне</p>'
        card = self.parser.parse_article(html, "tsblm2022")
        assert card.dictionary_name == "Тлумачальны слоўнік (2022)"
