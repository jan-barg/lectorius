import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';
import path from 'path';

export default defineConfig(({ mode }) => {
	const rootDir = path.resolve(import.meta.dirname, '../..');
	const env = loadEnv(mode, rootDir, '');

	for (const [key, value] of Object.entries(env)) {
		if (process.env[key] === undefined) {
			process.env[key] = value;
		}
	}

	return {
		plugins: [sveltekit()]
	};
});
