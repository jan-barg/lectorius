export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				primary: '#6366f1',
				secondary: '#a855f7',
				background: '#0f0f0f',
				surface: '#1a1a1a',
				text: '#fafafa',
				muted: '#71717a'
			},
			fontFamily: {
				sans: ['Inter', 'system-ui', 'sans-serif']
			}
		}
	},
	plugins: []
};
