import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import OpenAI from 'openai';
import { env } from '$env/dynamic/private';

let supabase: SupabaseClient | null = null;
let openai: OpenAI | null = null;

function getSupabase(): SupabaseClient {
	if (!supabase) {
		if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_KEY) {
			throw new Error('Missing SUPABASE_URL or SUPABASE_SERVICE_KEY');
		}
		supabase = createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_KEY);
	}
	return supabase;
}

function getOpenAI(): OpenAI {
	if (!openai) {
		if (!env.OPENAI_API_KEY) throw new Error('Missing OPENAI_API_KEY');
		openai = new OpenAI({ apiKey: env.OPENAI_API_KEY });
	}
	return openai;
}

/**
 * Query pgvector for semantically similar chunks, filtered to avoid spoilers.
 */
export async function queryRAG(
	bookId: string,
	question: string,
	maxChunkIndex: number,
	limit: number = 5
): Promise<{ chunk_id: string; chunk_index: number; chapter_id: string }[]> {
	const embeddingResponse = await getOpenAI().embeddings.create({
		model: 'text-embedding-3-small',
		input: question
	});
	const queryEmbedding = embeddingResponse.data[0].embedding;

	const { data, error } = await getSupabase().rpc('match_embeddings', {
		query_embedding: queryEmbedding,
		match_book_id: bookId,
		max_chunk_index: maxChunkIndex,
		match_count: limit
	});

	if (error) {
		console.error('RAG query failed:', error);
		return [];
	}

	return data || [];
}
