<script lang="ts">
	import { settings, type Theme } from '$lib/stores/settings';

	const options: { value: Theme; label: string }[] = [
		{ value: 'system', label: 'System' },
		{ value: 'light', label: 'Light' },
		{ value: 'dark', label: 'Dark' }
	];

	$: current = $settings.theme;
</script>

<div class="relative flex rounded-xl bg-text/[0.04] dark:bg-white/[0.04] p-1">
	<div
		class="absolute top-1 bottom-1 rounded-lg bg-accent shadow-md shadow-accent/15 transition-all duration-300 ease-out"
		style="width: calc((100% - 0.5rem) / 3); left: calc({options.findIndex((o) => o.value === current)} * (100% - 0.5rem) / 3 + 0.25rem);"
	></div>

	{#each options as opt}
		<button
			class="relative z-10 flex-1 rounded-lg px-4 py-2.5 text-xs font-semibold tracking-wide transition-colors duration-300
				{current === opt.value ? 'text-white' : 'text-muted hover:text-text'}"
			onclick={() => settings.setTheme(opt.value)}
		>
			{opt.label}
		</button>
	{/each}
</div>
