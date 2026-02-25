<script lang="ts">
	import { userName } from '$lib/stores/user';

	const hour = new Date().getHours();
	const SLOT = '%%NAME%%';

	const pools = {
		late: [`Fancy a lullaby, ${SLOT}?`, `Trouble sleeping, ${SLOT}?`],
		morning: ['Morning, pal.', `How's your coffee, ${SLOT}?`],
		default: [`Hello there, ${SLOT}`, `What are we reading, ${SLOT}?`, 'The book worm is back!']
	};

	const noNamePools = {
		late: ['Fancy a lullaby?', 'Up late reading?'],
		morning: ['Morning, pal.', 'Good morning!'],
		default: ['Hello there!', 'What are we reading today?', 'The book worm is back!']
	};

	const key: 'late' | 'morning' | 'default' =
		hour >= 22 || hour < 4 ? 'late' : hour < 12 ? 'morning' : 'default';
	const idx = Math.floor(Math.random() * pools[key].length);

	let name = $derived($userName);
	let greeting = $derived(
		name
			? pools[key][idx]
			: noNamePools[key][Math.min(idx, noNamePools[key].length - 1)]
	);
	let hasName = $derived(name !== '' && greeting.includes(SLOT));
	let parts = $derived(hasName ? greeting.split(SLOT) : [greeting]);
</script>

<h1 class="font-outfit text-3xl md:text-5xl font-light text-text drop-shadow-sm">
	{#if hasName}
		{parts[0]}<span class="font-serif italic text-accent font-bold">{name}</span>{parts[1]}
	{:else}
		{greeting}
	{/if}
</h1>
