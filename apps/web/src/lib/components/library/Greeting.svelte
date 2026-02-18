<script lang="ts">
	const name = 'Jan';
	const hour = new Date().getHours();

	const pools = {
		late: [`Fancy a lullaby, ${name}?`, `Trouble sleeping, ${name}?`],
		morning: ['Morning, pal.', `How's your coffee, ${name}?`],
		default: [`Hello there, ${name}`, `What are we reading, ${name}?`, 'The book worm is back!']
	};

	function pick(): string {
		let pool: string[];
		if (hour >= 22 || hour < 4) pool = pools.late;
		else if (hour < 12) pool = pools.morning;
		else pool = pools.default;
		return pool[Math.floor(Math.random() * pool.length)];
	}

	const greeting = pick();
</script>

<h1 class="text-3xl font-bold text-text">{greeting}</h1>
