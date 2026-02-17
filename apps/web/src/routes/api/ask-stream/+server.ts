import type { RequestHandler } from './$types';
import { toFile } from 'openai';
import { env } from '$env/dynamic/private';
import { getOpenAI, getAnthropic } from '$lib/server/clients';
import type { Chapter, Chunk } from '$lib/types';
import { getRecentChunks, getCurrentCheckpoint } from '$lib/server/context';
import { queryRAG } from '$lib/server/rag';
import { buildSystemPrompt, buildUserMessage, shouldUseRAG } from '$lib/server/prompts';
import { generateSpeech } from '$lib/server/tts';

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
	console.log(`[stream] === Starting streaming Q&A ===`);

	const body = await request.json();
	const { book_id, chunk_index, audio_base64, book, chapters, chunks, playback_map, checkpoints } =
		body;

	if (!book_id || !chunk_index || !audio_base64) {
		return sseError('Missing required fields', 'error');
	}

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

	console.log(`[stream] Question: "${question}" (${Date.now() - t0}ms)`);

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

	console.log(`[stream] Context assembled (${Date.now() - t0}ms)`);

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
							console.log(
								`[stream] TTS: "${sentence.substring(0, 50)}" (${Date.now() - t0}ms)`
							);
							const audio = await generateSpeech(sentence);
							send({ type: 'audio', text: sentence, audio });
						}
					}
				}

				// Flush remaining text
				if (buffer.trim()) {
					console.log(
						`[stream] TTS remaining: "${buffer.trim().substring(0, 50)}" (${Date.now() - t0}ms)`
					);
					const audio = await generateSpeech(buffer.trim());
					send({ type: 'audio', text: buffer.trim(), audio });
				}

				console.log(`[stream] Complete (${Date.now() - t0}ms)`);
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
	const abbrevs = new Set(['Mr', 'Mrs', 'Ms', 'Dr', 'Jr', 'Sr', 'Prof', 'St', 'vs', 'etc']);
	const extracted: string[] = [];
	let start = 0;

	for (let i = 0; i < text.length - 2; i++) {
		const ch = text[i];
		if (ch !== '.' && ch !== '!' && ch !== '?') continue;
		if (!/\s/.test(text[i + 1]) || text[i + 2] < 'A' || text[i + 2] > 'Z') continue;

		// Abbreviation check for periods
		if (ch === '.') {
			const before = text.slice(start, i);
			const lastWord = before.match(/(\w+)$/)?.[1];
			if (lastWord && abbrevs.has(lastWord)) continue;
		}

		const sentence = text.slice(start, i + 1).trim();
		if (sentence.length >= 10) {
			extracted.push(sentence);
		}
		start = i + 2;
	}

	const remaining = text.slice(start).trim();
	return { extracted, remaining };
}
