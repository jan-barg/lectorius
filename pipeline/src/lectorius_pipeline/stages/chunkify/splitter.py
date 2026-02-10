"""Text splitting utilities."""

import logging
import re

logger = logging.getLogger(__name__)

# Sentence splitting pattern (fallback)
SENTENCE_END_PATTERN = re.compile(
    r"(?<=[.!?])(?<![A-Z]\.)(?<!Mr\.)(?<!Mrs\.)(?<!Ms\.)(?<!Dr\.)(?<!Jr\.)(?<!Sr\.)\s+(?=[A-Z\"])"
)

# Pattern to check if text ends with sentence-ending punctuation
# Matches: .!? optionally followed by closing quotes/brackets
SENTENCE_END_CHECK = re.compile(r'[.!?]["\'\u201d\u2019\u00bb\])\}]*\s*$')


def ends_with_sentence_punctuation(text: str) -> bool:
    """
    Check if text ends with sentence-ending punctuation.

    Returns True if text ends with . ! or ? optionally followed by
    closing quotes like " ' » ) ] }
    """
    return bool(SENTENCE_END_CHECK.search(text))


def split_into_sentences_regex(text: str) -> list[str]:
    """
    Split text into sentences using regex.

    This is the fallback splitter when spacy is unavailable.
    """
    if not text.strip():
        return []

    sentences = SENTENCE_END_PATTERN.split(text)
    return [s.strip() for s in sentences if s.strip()]


def split_into_sentences_spacy(text: str, nlp) -> list[str]:
    """
    Split text into sentences using spacy.

    Args:
        text: Text to split
        nlp: Loaded spacy model
    """
    if not text.strip():
        return []

    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def load_spacy_model(model_name: str = "en_core_web_sm"):
    """
    Load spacy model, return None if unavailable.

    Returns:
        Loaded spacy model or None
    """
    try:
        import spacy

        return spacy.load(model_name)
    except ImportError:
        logger.warning("spacy not installed, using regex sentence splitter")
        return None
    except OSError:
        logger.warning("spacy model %s not found, using regex sentence splitter", model_name)
        return None


def split_text_into_paragraphs(text: str) -> list[str]:
    """
    Split text into paragraphs on double newlines.

    Returns:
        List of paragraph texts
    """
    # Split on 2+ newlines
    paragraphs = re.split(r"\n\n+", text)
    return [p.strip() for p in paragraphs if p.strip()]


def unwrap_hard_wrapped_lines(paragraph: str) -> str:
    """
    Unwrap hard-wrapped lines within a paragraph.

    Joins lines that don't end with sentence-ending punctuation.
    """
    lines = paragraph.split("\n")
    if len(lines) <= 1:
        return paragraph

    result: list[str] = []
    current = lines[0]

    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        # If current line ends with sentence punctuation, keep separate
        if current.rstrip().endswith((".", "!", "?", ":", ";", '"', "'")):
            result.append(current)
            current = line
        else:
            # Join with space
            current = current.rstrip() + " " + line

    if current:
        result.append(current)

    return " ".join(result)
