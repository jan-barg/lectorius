"""Prompt templates for memory checkpoint generation."""

CHECKPOINT_PROMPT = """\
You are summarizing a book for a reading assistant. Update the running summary \
and entity tracking based on new content.

PREVIOUS STATE:
{previous_checkpoint}

NEW CONTENT (chunks {start_chunk} to {end_chunk}):
\"\"\"
{chunk_texts}
\"\"\"

Return ONLY valid JSON (no markdown, no explanation) with this exact schema:
{{
  "summary": "2-3 paragraph summary of story so far, including this new section",
  "entities": {{
    "people": [
      {{"name": "...", "aliases": ["..."], "role": "protagonist|antagonist|supporting|mentioned", "description": "...", "first_chunk": N, "last_chunk": N}}
    ],
    "places": [
      {{"name": "...", "description": "...", "first_chunk": N, "last_chunk": N}}
    ],
    "open_threads": [
      {{"id": "thread_001", "description": "...", "status": "open|resolved", "introduced_chunk": N, "last_updated_chunk": N}}
    ]
  }}
}}

Rules:
- Update last_chunk/last_updated_chunk for existing entities seen in this section
- Mark threads "resolved" when concluded
- Never include events beyond chunk {end_chunk}
- Keep summary concise but complete — it must stand alone as a recap
- People roles: protagonist, antagonist, supporting, mentioned
- Thread IDs: thread_001, thread_002, etc. (sequential)
- If this is the first checkpoint, establish all entities from scratch
"""
