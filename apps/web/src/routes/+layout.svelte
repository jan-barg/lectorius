<script lang="ts">
	import "../app.css";
	import SettingsPanel from "$lib/components/settings/SettingsPanel.svelte";
	import { settings } from "$lib/stores/settings";
	import { onMount } from "svelte";

	let settingsOpen = false;

	onMount(() => {
		settings.init();
	});
</script>

<div
	class="relative min-h-screen bg-background transition-colors duration-300 isolate"
>
	<!-- Ambient Glow Background -->
	<div
		class="pointer-events-none fixed left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 h-[300px] w-[800px] rounded-full bg-accent/15 blur-[120px] dark:bg-accent/10 z-[-1]"
	></div>

	<!-- Top bar -->
	<nav
		class="fixed top-4 inset-x-4 sm:inset-x-8 max-w-6xl mx-auto z-50 rounded-full bg-surface/70 backdrop-blur-md border border-white/20 dark:border-white/5 shadow-sm px-6 py-3 flex justify-between items-center"
	>
		<a href="/" class="text-lg font-bold text-text">lectorius</a>
		<button
			class="rounded-lg p-2 text-muted transition-colors hover:bg-surface hover:text-text"
			on:click={() => (settingsOpen = true)}
			aria-label="Settings"
		>
			<svg
				class="h-5 w-5"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
				/>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
				/>
			</svg>
		</button>
	</nav>

	<main class="w-full max-w-6xl mx-auto px-4 sm:px-8 xl:px-12 pt-24 pb-12">
		<slot />
	</main>

	<SettingsPanel open={settingsOpen} onClose={() => (settingsOpen = false)} />
</div>
