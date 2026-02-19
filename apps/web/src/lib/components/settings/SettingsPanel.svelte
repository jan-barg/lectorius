<script lang="ts">
	import { fly, fade } from 'svelte/transition';
	import ThemeSwitcher from './ThemeSwitcher.svelte';

	export let open = false;
	export let onClose: () => void;

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onClose();
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if open}
	<!-- Backdrop -->
	<button
		class="fixed inset-0 z-40 bg-black/50"
		on:click={onClose}
		aria-label="Close settings"
		transition:fade={{ duration: 200 }}
	></button>

	<!-- Panel -->
	<div
		class="fixed top-0 right-0 z-50 h-full w-80 bg-surface p-6 shadow-xl"
		transition:fly={{ x: 320, duration: 300, opacity: 1 }}
	>
		<div class="mb-6 flex items-center justify-between">
			<h2 class="text-lg font-semibold text-text">Settings</h2>
			<button class="text-muted hover:text-text" on:click={onClose} aria-label="Close">
				<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div class="space-y-6">
			<div>
				<span class="mb-2 block text-sm font-medium text-muted">Theme</span>
				<ThemeSwitcher />
			</div>
		</div>
	</div>
{/if}
