from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpArtifacts, NlpEngine
from presidio_analyzer.recognizer_registry import RecognizerRegistry
import spacy


class BlankVietnameseNlpEngine(NlpEngine):
    """Minimal Vietnamese NLP engine for regex-based Presidio recognizers."""

    def __init__(self):
        self.nlp = None

    def load(self) -> None:
        self.nlp = spacy.blank("xx")

    def is_loaded(self) -> bool:
        return self.nlp is not None

    def process_text(self, text: str, language: str) -> NlpArtifacts:
        doc = self.nlp(text)
        return NlpArtifacts(
            entities=[],
            tokens=doc,
            tokens_indices=[token.idx for token in doc],
            lemmas=[token.text.lower() for token in doc],
            nlp_engine=self,
            language=language,
        )

    def process_batch(self, texts, language: str, batch_size: int = 1, n_process: int = 1, **kwargs):
        for text in texts:
            yield text, self.process_text(text, language)

    def is_stopword(self, word: str, language: str) -> bool:
        return False

    def is_punct(self, word: str, language: str) -> bool:
        return all(char in ".,;:!?()[]{}'\"-" for char in word)

    def get_supported_entities(self) -> list:
        return []

    def get_supported_languages(self) -> list:
        return ["vi"]


def build_vietnamese_analyzer() -> AnalyzerEngine:
    """Build a Presidio analyzer with Vietnamese-specific recognizers."""
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[Pattern(
            name="cccd_pattern",
            regex=r"(?<!\d)\d{11,12}(?!\d)",
            score=0.9,
        )],
        context=["cccd", "can cuoc", "can cuoc cong dan", "chung minh", "cmnd"],
        supported_language="vi",
    )

    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[Pattern(
            name="vn_phone",
            regex=r"(?<!\d)0?[35789]\d{8}(?!\d)",
            score=0.85,
        )],
        context=["dien thoai", "sdt", "phone", "lien he"],
        supported_language="vi",
    )

    email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        patterns=[Pattern(
            name="email",
            regex=r"\b[\w.!#$%&'*+/=?^`{|}~-]+@[\w-]+(?:\.[\w-]+)+\b",
            score=0.8,
        )],
        context=["email", "mail"],
        supported_language="vi",
    )

    person_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        patterns=[Pattern(
            name="vietnamese_person_name",
            regex=r"\b(?:[\p{Lu}][\p{L}]+|[\p{Lu}])(?:\s+(?:[\p{Lu}][\p{L}]+|[\p{Lu}])){1,4}\b",
            score=0.7,
        )],
        context=["benh nhan", "bac si", "ho ten", "ten"],
        supported_language="vi",
    )

    registry = RecognizerRegistry(supported_languages=["vi"])
    registry.add_recognizer(cccd_recognizer)
    registry.add_recognizer(phone_recognizer)
    registry.add_recognizer(email_recognizer)
    registry.add_recognizer(person_recognizer)

    return AnalyzerEngine(
        registry=registry,
        nlp_engine=BlankVietnameseNlpEngine(),
        supported_languages=["vi"],
    )


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """Detect PII in Vietnamese text."""
    return analyzer.analyze(
        text=str(text),
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"],
    )
