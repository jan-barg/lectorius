<script lang="ts">
	import { userName } from '$lib/stores/user';
	import { fade, fly } from 'svelte/transition';

	interface Props {
		onComplete: () => void;
	}

	let { onComplete }: Props = $props();

	let inputValue = $state('');

	function handleSubmit() {
		const trimmed = inputValue.trim();
		if (!trimmed) return;
		userName.setName(trimmed);
		onComplete();
	}
</script>

<div
	class="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-sm"
	transition:fade={{ duration: 300 }}
>
	<div class="w-full max-w-md px-6" transition:fly={{ y: 30, duration: 400 }}>
		<div
			class="rounded-2xl border border-white/10 bg-surface p-8 shadow-2xl space-y-6 text-center"
		>
			<h1 class="font-outfit text-3xl font-light text-text">
				Welcome to <span class="font-serif italic text-accent font-bold">Lectorius</span>
			</h1>
			<p class="text-sm text-muted">What's your name?</p>
			<!-- svelte-ignore a11y_autofocus -->
			<input
				type="text"
				bind:value={inputValue}
				onkeydown={(e) => e.key === 'Enter' && handleSubmit()}
				placeholder="Your name"
				class="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-center text-lg text-text placeholder:text-muted/50 outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/30 transition-colors"
				autofocus
			/>
			<button
				onclick={handleSubmit}
				disabled={!inputValue.trim()}
				class="w-full rounded-xl bg-accent px-6 py-3 text-sm font-medium text-white transition-all hover:bg-accent/80 disabled:opacity-40 disabled:cursor-not-allowed"
			>
				Continue
			</button>
		</div>
	</div>
</div>
