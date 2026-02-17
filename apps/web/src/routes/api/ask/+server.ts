import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import OpenAI, { toFile } from 'openai';
import Anthropic from '@anthropic-ai/sdk';
import { env } from '$env/dynamic/private';
import { getBookDetail } from '$lib/server/storage';
import type { BookMeta, Chapter, Chunk, PlaybackMapEntry, MemoryCheckpoint } from '$lib/types';
import { getRecentChunks, getCurrentCheckpoint } from '$lib/server/context';
import { queryRAG } from '$lib/server/rag';
import { buildSystemPrompt, buildUserMessage, shouldUseRAG } from '$lib/server/prompts';

let openai: OpenAI | null = null;
let anthropic: Anthropic | null = null;

function getOpenAI(): OpenAI {
	if (!openai) {
		if (!env.OPENAI_API_KEY) throw new Error('Missing OPENAI_API_KEY');
		openai = new OpenAI({ apiKey: env.OPENAI_API_KEY });
	}
	return openai;
}

function getAnthropic(): Anthropic {
	if (!anthropic) {
		if (!env.ANTHROPIC_API_KEY) throw new Error('Missing ANTHROPIC_API_KEY');
		anthropic = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });
	}
	return anthropic;
}

function fallbackUrl(id: string): string {
	return `${env.SUPABASE_URL}/storage/v1/object/public/system/audio/${id}.mp3`;
}

export const POST: RequestHandler = async ({ request }) => {
	const timings: Record<string, number> = {};
	const t0 = Date.now();
	console.log(`[ask] === Starting Q&A ===`);

	try {
		// 1. VALIDATE REQUEST
		const body = await request.json();
		const { book_id, chunk_index, chunk_time_ms, audio_base64 } = body;
		timings['1_parse_request'] = Date.now() - t0;

		if (!book_id || !chunk_index || !audio_base64) {
			return json(
				{ success: false, error: 'Missing required fields', fallback_audio_url: fallbackUrl('error') },
				{ status: 400 }
			);
		}

		// 2. LOAD BOOK DATA (prefer client-provided data, fallback to fetch)
		let t = Date.now();
		let book: BookMeta, chapters: Chapter[], chunks: Chunk[], playback_map: PlaybackMapEntry[], checkpoints: MemoryCheckpoint[];

		if (body.book && body.chapters && body.chunks && body.playback_map && body.checkpoints) {
			({ book, chapters, chunks, playback_map, checkpoints } = body);
			console.log(`[ask] Using client-provided book data (skipped fetch)`);
		} else {
			try {
				const bookData = await getBookDetail(book_id);
				({ book, chapters, chunks, playback_map, checkpoints } = bookData);
				console.log(`[ask] Fetched book data from storage (fallback)`);
			} catch {
				return json(
					{ success: false, error: 'Book not found', fallback_audio_url: fallbackUrl('error') },
					{ status: 404 }
				);
			}
		}
		timings['2_load_book'] = Date.now() - t;
		const totalChunks = chunks.length;

		if (chunk_index < 1 || chunk_index > totalChunks) {
			return json(
				{ success: false, error: 'Invalid chunk index', fallback_audio_url: fallbackUrl('error') },
				{ status: 400 }
			);
		}

		// 3. TRANSCRIBE AUDIO (Whisper)
		t = Date.now();
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
			console.error('Whisper failed:', e);
			return json({
				success: false,
				error: 'Transcription failed',
				fallback_audio_url: fallbackUrl('error')
			});
		}
		timings['3_whisper'] = Date.now() - t;

		if (!question || question.length < 2) {
			return json({
				success: false,
				error: 'Could not understand audio',
				fallback_audio_url: fallbackUrl('error')
			});
		}

		console.log(`[ask] Question: "${question}"`);

		// 4. EARLY EXIT — not enough context
		if (chunk_index < 5) {
			return json({
				success: false,
				error: 'Not enough context',
				fallback_audio_url: fallbackUrl('no_context_yet')
			});
		}

		// 5. ASSEMBLE CONTEXT
		t = Date.now();
		const recentChunks = getRecentChunks(chunks, playback_map, chunk_index, 60000);
		const recentText = recentChunks.map((c) => c.text).join('\n\n');
		const checkpoint = getCurrentCheckpoint(checkpoints, chunk_index);
		timings['4_context_assembly'] = Date.now() - t;

		// 6. RAG QUERY (if needed)
		t = Date.now();
		let ragChunks: { text: string; chapter_title: string }[] = [];
		if (shouldUseRAG(question)) {
			const ragResults = await queryRAG(book_id, question, chunk_index, 5);

			ragChunks = ragResults
				.map((r) => {
					const chunk = chunks.find((c) => c.chunk_id === r.chunk_id);
					const chapter = chapters.find((ch) => ch.chapter_id === r.chapter_id);
					return {
						text: chunk?.text || '',
						chapter_title: chapter?.title || 'Unknown Chapter'
					};
				})
				.filter((r) => r.text);
		}
		timings['5_rag'] = Date.now() - t;

		// 7. BUILD PROMPTS
		const systemPrompt = buildSystemPrompt(
			book.title,
			book.author,
			book.book_type,
			chunk_index,
			totalChunks
		);

		const userMessage = buildUserMessage(recentText, checkpoint, ragChunks, question);

		// 8. CALL CLAUDE
		t = Date.now();
		let answerText: string;
		try {
			const response = await getAnthropic().messages.create({
				model: 'claude-sonnet-4-20250514',
				max_tokens: 500,
				system: systemPrompt,
				messages: [{ role: 'user', content: userMessage }]
			});

			answerText =
				response.content[0].type === 'text' ? response.content[0].text : '';
		} catch (e) {
			console.error('Claude failed:', e);
			return json({
				success: false,
				error: 'LLM request failed',
				fallback_audio_url: fallbackUrl('error')
			});
		}
		timings['6_claude'] = Date.now() - t;

		console.log(`[ask] Answer: ${answerText}`);
		console.log(`[ask] Answer length: ${answerText.length} chars, ~${answerText.split(' ').length} words`);

		// 9. GENERATE SPEECH (OpenAI TTS)
		t = Date.now();
		let answerAudioBase64: string;
		try {
			const speech = await getOpenAI().audio.speech.create({
				model: 'tts-1',
				voice: 'alloy',
				input: answerText
			});

			const audioBuffer = Buffer.from(await speech.arrayBuffer());
			answerAudioBase64 = audioBuffer.toString('base64');
		} catch (e) {
			console.error('TTS failed:', e);
			return json({
				success: false,
				error: 'Speech generation failed',
				fallback_audio_url: fallbackUrl('error')
			});
		}
		timings['7_tts'] = Date.now() - t;

		// 10. RETURN SUCCESS
		timings['8_total'] = Date.now() - t0;

		console.log(`[ask] === Timings ===`);
		Object.entries(timings).forEach(([k, v]) => console.log(`[ask]   ${k}: ${v}ms`));

		return json({
			success: true,
			question_text: question,
			answer_text: answerText,
			answer_audio: answerAudioBase64
		});
	} catch (e) {
		console.error('Unexpected error:', e);
		return json({
			success: false,
			error: 'Internal error',
			fallback_audio_url: fallbackUrl('error')
		});
	}
};
