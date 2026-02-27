import type { Handle } from '@sveltejs/kit';
import { json } from '@sveltejs/kit';
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';
import { env } from '$env/dynamic/private';
import { getSupabase } from '$lib/server/clients';

let ratelimit: Ratelimit | null = null;

function getRatelimit(): Ratelimit {
	if (!ratelimit) {
		if (!env.UPSTASH_REDIS_REST_URL || !env.UPSTASH_REDIS_REST_TOKEN) {
			throw new Error('Missing UPSTASH_REDIS_REST_URL or UPSTASH_REDIS_REST_TOKEN');
		}
		ratelimit = new Ratelimit({
			redis: new Redis({
				url: env.UPSTASH_REDIS_REST_URL,
				token: env.UPSTASH_REDIS_REST_TOKEN
			}),
			limiter: Ratelimit.slidingWindow(60, '1 h'),
			analytics: true
		});
	}
	return ratelimit;
}

export const handle: Handle = async ({ event, resolve }) => {
	if (event.url.pathname !== '/api/ask' || event.request.method !== 'POST') {
		return resolve(event);
	}

	const ip = event.getClientAddress();
	const accessCode = event.cookies.get('lectorius_access');

	// 1. Rate limit check (applies to all users)
	try {
		const identifier = accessCode || `ip:${ip}`;
		const { success } = await getRatelimit().limit(identifier);
		if (!success) {
			return json({ error: 'Too many questions. Try again later.' }, { status: 429 });
		}
	} catch (e) {
		console.error('[hooks] Rate limit check failed:', e);
		// Fail open — Redis outage should not block users
	}

	// 2. Validate access code cookie against the database
	let validAccess = false;
	if (accessCode) {
		try {
			const { data } = await getSupabase()
				.from('access_codes')
				.select('code')
				.eq('code', accessCode)
				.maybeSingle();

			if (data) {
				validAccess = true;
			} else {
				event.cookies.delete('lectorius_access', { path: '/' });
			}
		} catch (e) {
			console.error('[hooks] Access code validation failed:', e);
			// Fall through to free-tier IP check
		}
	}

	// 3. Access check (only for users without valid access code)
	if (!validAccess) {
		try {
			const { count, error } = await getSupabase()
				.from('question_log')
				.select('*', { count: 'exact', head: true })
				.eq('ip', ip);

			if (error) {
				console.error('[hooks] Question count query failed:', error);
				return json({ error: 'Service temporarily unavailable' }, { status: 503 });
			} else if (count !== null && count >= 3) {
				return json({ error: 'Free limit reached' }, { status: 403 });
			}
		} catch (e) {
			console.error('[hooks] Access check failed:', e);
			return json({ error: 'Service temporarily unavailable' }, { status: 503 });
		}
	}

	return resolve(event);
};
