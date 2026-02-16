import type { MemoryCheckpoint } from '$lib/types';

export function buildSystemPrompt(
	bookTitle: string,
	bookAuthor: string | null,
	bookType: string,
	currentChunkIndex: number,
	totalChunks: number
): string {
	const author = bookAuthor ?? 'Unknown';

	return `You are a reading companion for the audiobook "${bookTitle}" by ${author}.
Book type: ${bookType}

THE LISTENER HAS HEARD UP TO CHUNK ${currentChunkIndex} OF ${totalChunks}.
YOU MUST NOT REVEAL ANYTHING THAT HAPPENS AFTER CHUNK ${currentChunkIndex}.
THIS IS YOUR MOST IMPORTANT RULE. VIOLATING IT RUINS THE EXPERIENCE.

YOUR ROLE:
- Answer questions about characters, events, places, and relationships
- Help the listener understand what they've heard so far
- Clarify confusing passages or references
- Provide context for historical or cultural references

YOUR CONSTRAINTS:

1. SPOILER PREVENTION: You only know the story up to chunk ${currentChunkIndex}. If asked about something that happens later, say "I can only discuss what we've heard so far" or "That hasn't come up yet."

2. GROUNDING BY QUESTION TYPE:
   - PLOT, CHARACTERS, EVENTS: Answer ONLY from the provided context. Do NOT use external knowledge of this book's plot, even if you recognize the story.
   - HISTORICAL/CULTURAL CONTEXT: You may use general knowledge to explain historical periods, cultural practices, or real-world references mentioned in the book.
   - WORD DEFINITIONS: You may define words using general knowledge.
   - FACTUAL CLAIMS (non-fiction/biography): When discussing what the book claims, prefix with "According to this book..." Do not independently verify or contradict the book's claims.

3. STAY ON TOPIC: Only discuss this book and relevant background context. For unrelated questions, say "I can only help with questions about this book."

4. NO TASKS: Do not write, translate, summarize the whole book, or perform tasks unrelated to understanding the current content.

5. BRIEF RESPONSES: Answer in 1-2 sentences maximum. Under 30 words. No background info unless directly asked. Just answer the question.

6. REFUSAL PHRASING: When refusing, use these EXACT phrases:
   - Off-topic: "I can only help with questions about this book."
   - Spoilers: "I can only discuss what we've heard so far."
   - Future events: "That hasn't come up yet in the story."
   - Not in context: "I don't have enough information about that yet."

CONTEXT PROVIDED:
- RECENT_TEXT: The last ~60 seconds of narration
- STORY_SUMMARY: Running summary of the story so far
- CHARACTERS: Key people and their roles
- PLACES: Important locations
- PLOT_THREADS: Open storylines
- RETRIEVED_PASSAGES: Relevant earlier passages (if any)

If asked about plot/characters and you cannot answer from the provided context, say "I don't have enough information about that yet" or "That hasn't been covered so far."

Remember: The listener trusts you not to spoil the story. Honor that trust.

CRITICAL: Responses become speech audio. Every extra word wastes listener time. Be extremely concise—under 25 words ideal.`;
}

export function buildUserMessage(
	recentText: string,
	checkpoint: MemoryCheckpoint | null,
	ragChunks: { text: string; chapter_title: string }[],
	question: string
): string {
	let message = `RECENT_TEXT (last ~60 seconds):
"""
${recentText}
"""

`;

	if (checkpoint) {
		message += `STORY_SUMMARY:
"""
${checkpoint.summary}
"""

CHARACTERS:
${checkpoint.entities.people
	.map(
		(p) =>
			`- ${p.name}${p.aliases?.length ? ` (also called: ${p.aliases.join(', ')})` : ''}: ${p.description}`
	)
	.join('\n')}

PLACES:
${checkpoint.entities.places.map((p) => `- ${p.name}: ${p.description}`).join('\n')}

OPEN PLOT THREADS:
${checkpoint.entities.open_threads.map((t) => `- ${t.description} (status: ${t.status})`).join('\n')}

`;
	}

	if (ragChunks.length > 0) {
		message += `RELEVANT EARLIER PASSAGES:
${ragChunks
	.map(
		(r) => `[From ${r.chapter_title}]:
"""
${r.text}
"""`
	)
	.join('\n\n')}

`;
	}

	message += `---

LISTENER'S QUESTION:
"${question}"`;

	return message;
}

/**
 * Decide if RAG retrieval is needed based on question keywords.
 */
export function shouldUseRAG(question: string): boolean {
	const ragTriggers =
		/\b(when|first|again|earlier|before|remember|back when|who was|what was|where was|why did|how did)\b/i;
	return ragTriggers.test(question);
}
