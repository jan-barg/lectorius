<script lang="ts">
	import "../app.css";
	import SettingsPanel from "$lib/components/settings/SettingsPanel.svelte";
	import MusicPlayer from "$lib/components/music/MusicPlayer.svelte";
	import { settings } from "$lib/stores/settings";
	import { fetchPlaylists } from "$lib/stores/music";
	import { onMount } from "svelte";

	let settingsOpen = false;

	onMount(() => {
		settings.init();
		fetchPlaylists();
	});
</script>

<div
	class="relative min-h-screen bg-background transition-colors duration-500 isolate"
>
	<!-- Ambient warm glow -->
	<div
		class="pointer-events-none fixed left-1/2 top-0 -translate-x-1/2 -translate-y-1/3 h-[500px] w-[900px] rounded-full bg-accent/8 blur-[150px] dark:bg-accent/5 z-[-1]"
	></div>

	<!-- Navigation -->
	<nav
		class="fixed top-0 inset-x-0 z-50 border-b border-text/[0.06] dark:border-white/[0.06] bg-background/80 backdrop-blur-xl"
	>
		<div class="max-w-6xl mx-auto px-6 sm:px-10 flex justify-between items-center h-14">
			<a href="/" class="font-display text-xl tracking-wide italic text-text transition-colors">Lectorius</a>
			<button
				class="rounded-full p-2 text-muted transition-all duration-200 hover:text-text hover:bg-text/5"
				onclick={() => (settingsOpen = !settingsOpen)}
				aria-label="Settings"
			>
				<svg
					class="h-[18px] w-[18px]"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
					/>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
					/>
				</svg>
			</button>
		</div>
	</nav>

	<main class="w-full max-w-6xl mx-auto px-6 sm:px-10 pt-20 pb-16">
		<slot />
	</main>

	<MusicPlayer />
	<SettingsPanel open={settingsOpen} onClose={() => (settingsOpen = false)} />
</div>
