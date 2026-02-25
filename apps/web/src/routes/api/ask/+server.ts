import type { RequestHandler } from './$types';
import { toFile } from 'openai';
import { env } from '$env/dynamic/private';
import { getOpenAI, getAnthropic, getSupabase } from '$lib/server/clients';
import type { Chapter, Chunk } from '$lib/types';
import { getCachedBook } from '$lib/server/book-cache';
import { getRecentChunks, getCurrentCheckpoint } from '$lib/server/context';
import { queryRAG } from '$lib/server/rag';
import { buildSystemPrompt, buildUserMessage, shouldUseRAG } from '$lib/server/prompts';
import { generateSpeech } from '$lib/server/tts';

const debug = env.DEBUG_LOGGING === 'true';
function debugLog(...args: unknown[]) { if (debug) console.log(...args); }

function fallbackUrl(id: string): string {
	return `${env.SUPABASE_URL}/storage/v1/object/public/system/audio/${id}.mp3`;
}

function sseError(error: string, fallbackId: string): Response {
	const data = JSON.stringify({
		type: 'error',
		error,
		fallback_audio_url: fallbackUrl(fallbackId)
	});
	return new Response(`data: ${data}\n\n`, {
		headers: { 'Content-Type': 'text/event-stream' }
	});
}

export const POST: RequestHandler = async ({ request }) => {
	const t0 = Date.now();
	debugLog(`[stream] === Starting streaming Q&A ===`);

	const forwarded = request.headers.get('x-forwarded-for');
	const clientIP = forwarded ? forwarded.split(',')[0].trim() : '127.0.0.1';
	const userName = request.headers.get('x-user-name') || '';

	const { book_id, chunk_index, audio_base64 } = await request.json();

	if (!book_id || !chunk_index || !audio_base64) {
		return sseError('Missing required fields', 'error');
	}

	const bookData = await getCachedBook(book_id);
	if (!bookData) {
		return sseError('Book not found', 'error');
	}
	const { book, chapters, chunks, playback_map, checkpoints } = bookData;

	// 1. Transcribe
	let question: string;
	try {
		const audioBuffer = Buffer.from(audio_base64, 'base64');
		const audioFile = await toFile(audioBuffer, 'audio.webm', { type: 'audio/webm' });
		const transcription = await getOpenAI().audio.transcriptions.create({
			file: audioFile,
			model: 'whisper-1'
		});
		question = transcription.text.trim();
	} catch (e) {
		console.error('[stream] Whisper failed:', e);
		return sseError('Transcription failed', 'error');
	}

	if (!question || question.length < 2) {
		return sseError('Could not understand audio', 'error');
	}

	if (chunk_index < 5) {
		return sseError('Not enough context', 'no_context_yet');
	}

	debugLog(`[stream] Question: "${question}" (${Date.now() - t0}ms)`);

	// 2. Context assembly
	const recentChunks = getRecentChunks(chunks, playback_map, chunk_index, 60000);
	const recentText = recentChunks.map((c: Chunk) => c.text).join('\n\n');
	const checkpoint = getCurrentCheckpoint(checkpoints, chunk_index);

	let ragChunks: { text: string; chapter_title: string }[] = [];
	if (shouldUseRAG(question)) {
		const ragResults = await queryRAG(book_id, question, chunk_index, 5);
		ragChunks = ragResults
			.map((r) => {
				const chunk = chunks.find((c: Chunk) => c.chunk_id === r.chunk_id);
				const chapter = chapters.find((ch: Chapter) => ch.chapter_id === r.chapter_id);
				return { text: chunk?.text || '', chapter_title: chapter?.title || '' };
			})
			.filter((r: { text: string }) => r.text);
	}

	const systemPrompt = buildSystemPrompt(
		book.title,
		book.author,
		book.book_type,
		chunk_index,
		chunks.length
	);
	const userMessage = buildUserMessage(recentText, checkpoint, ragChunks, question);

	debugLog(`[stream] Context assembled (${Date.now() - t0}ms)`);

	// 3. Stream Claude → sentence-by-sentence TTS
	const stream = new ReadableStream({
		async start(controller) {
			const encoder = new TextEncoder();
			const send = (data: object) => {
				controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
			};

			try {
				send({ type: 'question', text: question });

				let buffer = '';
				let fullAnswer = '';

				const claudeStream = getAnthropic().messages.stream({
					model: 'claude-sonnet-4-20250514',
					max_tokens: 500,
					system: systemPrompt,
					messages: [{ role: 'user', content: userMessage }]
				});

				for await (const event of claudeStream) {
					if (
						event.type === 'content_block_delta' &&
						event.delta.type === 'text_delta'
					) {
						buffer += event.delta.text;
						fullAnswer += event.delta.text;

						const { extracted, remaining } = extractSentences(buffer);
						buffer = remaining;

						for (const sentence of extracted) {
							debugLog(
								`[stream] TTS: "${sentence.substring(0, 50)}" (${Date.now() - t0}ms)`
							);
							const audio = await generateSpeech(sentence);
							send({ type: 'audio', text: sentence, audio });
						}
					}
				}

				// Flush remaining text
				if (buffer.trim()) {
					debugLog(
						`[stream] TTS remaining: "${buffer.trim().substring(0, 50)}" (${Date.now() - t0}ms)`
					);
					const audio = await generateSpeech(buffer.trim());
					send({ type: 'audio', text: buffer.trim(), audio });
				}

				debugLog(`[stream] Complete (${Date.now() - t0}ms)`);

				// Log question to database
				try {
					await getSupabase().from('question_log').insert({
						ip: clientIP,
						user_name: userName || null,
						book_id,
						question
					});
				} catch (e) {
					console.error('[stream] Failed to log question:', e);
				}

				send({ type: 'done', full_answer: fullAnswer });
				controller.close();
			} catch (error: unknown) {
				console.error('[stream] Error:', error);
				send({ type: 'error', fallback_audio_url: fallbackUrl('error') });
				controller.close();
			}
		}
	});

	return new Response(stream, {
		headers: {
			'Content-Type': 'text/event-stream',
			'Cache-Control': 'no-cache',
			Connection: 'keep-alive'
		}
	});
};

function extractSentences(text: string): { extracted: string[]; remaining: string } {
	const extracted: string[] = [];
	let remaining = text;

	const isUppercase = (c: string) => c >= 'A' && c <= 'Z';
	const isQuote = (c: string) =>
		c === '"' || c === "'" || c === '\u201C' || c === '\u2018' || c === '\u201D';

	const regex = /([^.!?]+[.!?])\s+/g;
	let match;
	let lastIndex = 0;

	while ((match = regex.exec(text)) !== null) {
		const sentence = match[1].trim();
		const afterMatch = text[regex.lastIndex];
		const afterMatchNext = text[regex.lastIndex + 1];

		const startsNewSentence =
			(afterMatch && isUppercase(afterMatch)) ||
			(afterMatch && isQuote(afterMatch) && afterMatchNext && isUppercase(afterMatchNext));

		if (sentence.length >= 15 && startsNewSentence) {
			extracted.push(sentence);
			lastIndex = regex.lastIndex;
		}
	}

	remaining = text.slice(lastIndex);
	return { extracted, remaining };
}
