import { getSupabase, getOpenAI } from '$lib/server/clients';

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
