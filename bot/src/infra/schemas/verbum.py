from pydantic import BaseModel


class VerbumArticle(BaseModel):
    ID: str
    Content: str
    DictionaryID: str


class VerbumPagination(BaseModel):
    Current: int
    Total: int
    Relation: str


class VerbumResponse(BaseModel):
    DictIDs: list[str]
    Q: str
    Articles: list[VerbumArticle]
    TermSuggestions: list[str]
    Pagination: VerbumPagination


class ParsedDefinition(BaseModel):
    number: int | None = None
    text: str
    examples: list[str] = []
    labels: list[str] = []


class ParsedCard(BaseModel):
    headword: str
    accent: str | None = None
    part_of_speech: str | None = None
    definitions: list[ParsedDefinition] = []
    phrases: list[str] = []
    raw_html: str
    dictionary_id: str
