"""LLM-assisted text analysis for ingest stage."""

import json
import logging

import anthropic

from lectorius_pipeline.errors import LLMAssistError
from lectorius_pipeline.schemas import LLMAnalysis

logger = logging.getLogger(__name__)

HEAD_SAMPLE_CHARS = 4000
TAIL_SAMPLE_CHARS = 3000


def run_llm_analysis(
    text: str,
    book_title: str | None,
    book_author: str | None,
    model: str = "claude-sonnet-4-20250514",
) -> LLMAnalysis:
    """
    Call Claude to analyze raw text structure.

    Sends head and tail samples of the text for analysis of narrative
    boundaries, junk patterns, chapter heading style, and anomalies.

    Args:
        text: Full normalized text
        book_title: Book title from metadata
        book_author: Author from metadata
        model: Claude model to use

    Returns:
        LLMAnalysis with structured results

    Raises:
        LLMAssistError: If the API call or response parsing fails
    """
    head, tail = _sample_text(text)
    prompt = _build_prompt(head, tail, len(text), book_title, book_author)

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
    except Exception as e:
        raise LLMAssistError(f"API call failed: {e}") from e

    analysis = _parse_response(response_text)
    analysis.model_used = model
    analysis.tokens_used = tokens_used

    logger.info(
        "LLM analysis: start='%s', end='%s', %d junk patterns, chapter='%s'",
        analysis.narrative_start_marker[:50],
        analysis.narrative_end_marker[:50],
        len(analysis.junk_patterns),
        analysis.chapter_heading_pattern[:50],
    )

    return analysis


def _sample_text(text: str) -> tuple[str, str]:
    """Extract head and tail samples from text."""
    head = text[:HEAD_SAMPLE_CHARS]
    if len(text) > HEAD_SAMPLE_CHARS + TAIL_SAMPLE_CHARS:
        tail = text[-TAIL_SAMPLE_CHARS:]
    else:
        tail = text[HEAD_SAMPLE_CHARS:]
    return head, tail


def _build_prompt(
    head: str,
    tail: str,
    total_chars: int,
    title: str | None,
    author: str | None,
) -> str:
    """Build the prompt for text analysis."""
    title_str = title or "Unknown"
    author_str = author or "Unknown"

    return f"""You are analyzing the raw text extracted from a digitized book for an audiobook pipeline.
The text has already had Gutenberg boilerplate removed, but may still contain:
- Front matter (title pages, dedication, epigraphs, illustration lists, publisher info)
- Back matter (printer colophons, transcriber notes, advertisement pages)
- Illustration captions or artifacts (e.g., "See larger view", "[Illustration: ...]")
- Drop cap artifacts (single capital letters on their own line at chapter starts)

Book title: {title_str}
Book author: {author_str}
Total text length: {total_chars} characters

FIRST {len(head)} CHARACTERS:
\"\"\"
{head}
\"\"\"

LAST {len(tail)} CHARACTERS:
\"\"\"
{tail}
\"\"\"

Analyze the text and return ONLY valid JSON (no markdown, no explanation) with this schema:
{{
  "narrative_start_marker": "<copy the exact line where the actual story/narrative prose begins — skip title pages, dedications, epigraphs, illustration lists, publisher info>",
  "narrative_end_marker": "<copy the exact line where the actual story/narrative prose ends — skip colophons, transcriber notes, printer info, advertisements>",
  "junk_patterns": ["<Python regex patterns for non-narrative artifacts to strip, e.g. illustration captions. Empty list if none found>"],
  "chapter_heading_pattern": "<Python regex pattern matching the chapter heading style used in this book, e.g. ^Chapter\\\\s+[IVXLC]+\\\\.?$>",
  "chapter_heading_examples": ["<2-3 example chapter headings copied from the text>"],
  "anomalies": ["<structural anomalies observed, e.g. drop cap letters on separate lines>"]
}}

Be precise with narrative_start_marker and narrative_end_marker — copy exact text from the samples.
For chapter_heading_pattern, provide a Python-compatible regex that matches ALL chapter headings in this book.
Escape backslashes properly for JSON (use \\\\ for a literal backslash in regex)."""


def _parse_response(response_text: str) -> LLMAnalysis:
    """Parse JSON response into LLMAnalysis model."""
    # Strip markdown code fences if present
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # skip opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMAssistError(f"Failed to parse LLM response as JSON: {e}") from e

    try:
        return LLMAnalysis.model_validate(data)
    except Exception as e:
        raise LLMAssistError(f"Failed to validate LLM response: {e}") from e
