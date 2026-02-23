<script lang="ts">
	import { fly, fade } from 'svelte/transition';
	import ThemeSwitcher from './ThemeSwitcher.svelte';
	import { clearAllReadingHistory } from '$lib/stores/reading-history';

	export let open = false;
	export let onClose: () => void;

	/** 'idle' | 'confirm' | 'feedback' */
	let state = 'idle';

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			if (state === 'confirm') {
				state = 'idle';
			} else {
				onClose();
			}
		}
	}

	function handleDelete() {
		clearAllReadingHistory();
		state = 'feedback';
		setTimeout(() => {
			state = 'idle';
		}, 2000);
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<!-- Backdrop -->
	<button
		class="fixed inset-0 z-40 bg-black/50"
		onclick={onClose}
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
			<button class="text-muted hover:text-text" onclick={onClose} aria-label="Close">
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

		<!-- Danger zone -->
		<div class="mt-10 border-t border-white/10 pt-6">
			<span class="mb-3 block text-xs font-medium uppercase tracking-wider text-muted">Danger Zone</span>

			<div class="relative grid [&>*]:col-start-1 [&>*]:row-start-1">
				<div class="transition-all duration-200 {state === 'idle' ? 'opacity-100' : 'pointer-events-none opacity-0'}">
					<button
						class="w-full rounded-lg bg-red-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-600"
						onclick={() => (state = 'confirm')}
					>
						Delete All Progress
					</button>
				</div>

				<div class="space-y-3 transition-all duration-200 {state === 'confirm' ? 'opacity-100' : 'pointer-events-none opacity-0'}">
					<p class="text-sm text-text">Are you sure you want to delete all book progress?</p>
					<div class="flex gap-2">
						<button
							class="rounded-lg bg-red-500 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-red-600"
							onclick={handleDelete}
						>
							Yes, delete
						</button>
						<button
							class="rounded-lg border border-white/10 px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:text-text"
							onclick={() => (state = 'idle')}
						>
							Cancel
						</button>
					</div>
				</div>

				<div class="flex items-center transition-all duration-200 {state === 'feedback' ? 'opacity-100' : 'pointer-events-none opacity-0'}">
					<p class="text-sm font-medium text-green-500">Progress deleted</p>
				</div>
			</div>
		</div>
	</div>
{/if}
