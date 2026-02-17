import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import OpenAI from 'openai';
import Anthropic from '@anthropic-ai/sdk';
import { env } from '$env/dynamic/private';

let supabase: SupabaseClient | null = null;
let openai: OpenAI | null = null;
let anthropic: Anthropic | null = null;

export function getSupabase(): SupabaseClient {
	if (!supabase) {
		if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_KEY) {
			throw new Error('Missing SUPABASE_URL or SUPABASE_SERVICE_KEY');
		}
		supabase = createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_KEY);
	}
	return supabase;
}

export function getOpenAI(): OpenAI {
	if (!openai) {
		if (!env.OPENAI_API_KEY) throw new Error('Missing OPENAI_API_KEY');
		openai = new OpenAI({ apiKey: env.OPENAI_API_KEY });
	}
	return openai;
}

export function getAnthropic(): Anthropic {
	if (!anthropic) {
		if (!env.ANTHROPIC_API_KEY) throw new Error('Missing ANTHROPIC_API_KEY');
		anthropic = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });
	}
	return anthropic;
}
