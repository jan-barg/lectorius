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
	class="fixed inset-0 z-50 flex items-center justify-center bg-background/90 backdrop-blur-md"
	transition:fade={{ duration: 400 }}
>
	<div class="w-full max-w-sm px-6" transition:fly={{ y: 20, duration: 500 }}>
		<div
			class="rounded-2xl border border-text/[0.06] dark:border-white/[0.06] bg-surface p-10 shadow-2xl shadow-black/10 dark:shadow-black/40 space-y-8 text-center"
		>
			<div class="space-y-3">
				<h1 class="font-display text-3xl font-light text-muted tracking-tight">
					Welcome to
					<br />
					<span class="text-4xl italic text-accent">Lectorius</span>
				</h1>
				<p class="text-sm text-muted font-medium">What should we call you?</p>
			</div>
			<!-- svelte-ignore a11y_autofocus -->
			<input
				type="text"
				bind:value={inputValue}
				onkeydown={(e) => e.key === 'Enter' && handleSubmit()}
				placeholder="Your name"
				class="w-full rounded-lg border border-text/[0.08] dark:border-white/[0.08] bg-background px-4 py-3 text-center text-base text-text placeholder:text-muted/40 outline-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10 transition-all duration-200"
				autofocus
			/>
			<button
				onclick={handleSubmit}
				disabled={!inputValue.trim()}
				class="w-full rounded-lg bg-accent px-6 py-3 text-sm font-semibold text-white transition-all duration-200 hover:brightness-110 disabled:opacity-30 disabled:cursor-not-allowed"
			>
				Continue
			</button>
		</div>
	</div>
</div>
