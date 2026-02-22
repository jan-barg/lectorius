<script lang="ts">
	import { settings, type Theme } from '$lib/stores/settings';

	const options: { value: Theme; label: string }[] = [
		{ value: 'system', label: 'System' },
		{ value: 'light', label: 'Light' },
		{ value: 'dark', label: 'Dark' }
	];

	$: current = $settings.theme;
</script>

<div class="relative flex rounded-lg bg-background p-1">
	<div
		class="absolute top-1 bottom-1 rounded-md bg-accent transition-all duration-200 ease-out"
		style="width: calc((100% - 0.5rem) / 3); left: calc({options.findIndex((o) => o.value === current)} * (100% - 0.5rem) / 3 + 0.25rem);"
	></div>

	{#each options as opt}
		<button
			class="relative z-10 flex-1 rounded-md px-4 py-1.5 text-sm font-medium transition-colors duration-200
				{current === opt.value ? 'text-white' : 'text-muted hover:text-text'}"
			onclick={() => settings.setTheme(opt.value)}
		>
			{opt.label}
		</button>
	{/each}
</div>
