import type { RequestHandler } from './$types';
import { json } from '@sveltejs/kit';
import { dev } from '$app/environment';
import { getSupabase } from '$lib/server/clients';

export const POST: RequestHandler = async ({ request, cookies, getClientAddress }) => {
	const { code, user_name } = await request.json();

	if (!code || typeof code !== 'string' || !code.trim()) {
		return json({ success: false, error: 'Missing code' }, { status: 400 });
	}

	const { data, error } = await getSupabase()
		.from('access_codes')
		.select('code')
		.eq('code', code.trim())
		.maybeSingle();

	if (error) {
		console.error('[verify-code] Supabase error:', error);
		return json({ success: false, error: 'Server error' }, { status: 500 });
	}

	if (!data) {
		return json({ success: false, error: 'Invalid code' }, { status: 401 });
	}

	try {
		await getSupabase().from('code_usage_log').insert({
			code: code.trim(),
			ip: getClientAddress(),
			user_name: (typeof user_name === 'string' && user_name.trim()) || null
		});
	} catch (e) {
		console.error('[verify-code] Failed to log usage:', e);
	}

	cookies.set('lectorius_access', code.trim(), {
		path: '/',
		httpOnly: true,
		secure: !dev,
		sameSite: 'lax',
		maxAge: 60 * 60 * 24 * 30 // 30 days
	});

	return json({ success: true });
};
