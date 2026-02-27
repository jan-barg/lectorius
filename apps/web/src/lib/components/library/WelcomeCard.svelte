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
	class="fixed inset-0 z-50 flex items-center justify-center bg-background/90 backdrop-blur-xl"
	transition:fade={{ duration: 500 }}
>
	<div class="w-full max-w-sm px-6" transition:fly={{ y: 24, duration: 600 }}>
		<div
			class="rounded-2xl border border-text/[0.05] dark:border-white/[0.05] bg-surface/95 backdrop-blur-2xl p-12 shadow-2xl shadow-black/10 dark:shadow-black/50 space-y-10 text-center"
		>
			<div class="space-y-4">
				<h1 class="font-display tracking-tight leading-[1.1]">
					<span class="block text-3xl font-extralight text-muted/70">Welcome to</span>
					<span class="block text-5xl italic text-accent font-light mt-1">Lectorius</span>
				</h1>
				<p class="text-sm text-muted/60 font-medium tracking-wide">What should we call you?</p>
			</div>
			<!-- svelte-ignore a11y_autofocus -->
			<input
				type="text"
				bind:value={inputValue}
				onkeydown={(e) => e.key === 'Enter' && handleSubmit()}
				placeholder="Your name"
				class="w-full rounded-xl border border-text/[0.06] dark:border-white/[0.06] bg-text/[0.02] dark:bg-white/[0.02] px-5 py-3.5 text-center text-base text-text placeholder:text-muted/30 outline-none focus:border-accent/30 focus:ring-2 focus:ring-accent/8 transition-all duration-300"
				autofocus
			/>
			<button
				onclick={handleSubmit}
				disabled={!inputValue.trim()}
				class="w-full rounded-xl bg-accent px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-accent/20 transition-all duration-300 hover:brightness-110 hover:shadow-xl hover:shadow-accent/25 disabled:opacity-30 disabled:shadow-none disabled:cursor-not-allowed"
			>
				Continue
			</button>
		</div>
	</div>
</div>
