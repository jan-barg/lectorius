<script lang="ts">
	import '../app.css';
	import SettingsPanel from '$lib/components/settings/SettingsPanel.svelte';
	import { settings } from '$lib/stores/settings';
	import { onMount } from 'svelte';

	let settingsOpen = false;

	onMount(() => {
		settings.init();
	});
</script>

<div class="min-h-screen bg-background transition-colors duration-300">
	<!-- Top bar -->
	<nav class="flex items-center justify-between px-4 py-3">
		<a href="/" class="text-lg font-bold text-text">lectorius</a>
		<button
			class="rounded-lg p-2 text-muted transition-colors hover:bg-surface hover:text-text"
			on:click={() => (settingsOpen = true)}
			aria-label="Settings"
		>
			<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
					d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
				/>
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
			</svg>
		</button>
	</nav>

	<slot />

	<SettingsPanel open={settingsOpen} onClose={() => (settingsOpen = false)} />
</div>
