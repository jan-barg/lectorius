export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	darkMode: 'class',
	theme: {
		extend: {
			colors: {
				background: 'rgb(var(--color-background) / <alpha-value>)',
				surface: 'rgb(var(--color-surface) / <alpha-value>)',
				text: 'rgb(var(--color-text) / <alpha-value>)',
				muted: 'rgb(var(--color-muted) / <alpha-value>)',
				accent: 'rgb(var(--color-accent) / <alpha-value>)'
			},
			fontFamily: {
				sans: ['Outfit', 'sans-serif'],
				serif: ['Merriweather', 'serif']
			}
		}
	},
	plugins: []
};
