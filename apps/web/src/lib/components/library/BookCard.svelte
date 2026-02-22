<script lang="ts">
	import type { BookListItem } from "$lib/types";
	import BookCardVideo from "./BookCardVideo.svelte";
	import ProgressOverlay from "./ProgressOverlay.svelte";

	export let book: BookListItem;
	export let progress: number | null = null;

	let hovering = false;

	$: isComingSoon = book.status === "coming_soon";

	function formatDuration(ms: number): string {
		const hours = Math.floor(ms / 3600000);
		const minutes = Math.floor((ms % 3600000) / 60000);
		if (hours > 0) return `${hours}h ${minutes}m`;
		return `${minutes}m`;
	}
</script>

{#snippet cardContent()}
	{#if progress !== null && !isComingSoon}
		<div class="absolute bottom-0 left-0 w-full z-[15]">
			<ProgressOverlay percentage={progress} />
		</div>
	{/if}

	<div
		class="absolute bottom-0 inset-x-0 h-2/5 bg-gradient-to-t from-black/90 via-black/40 to-transparent backdrop-blur-md [mask-image:linear-gradient(to_top,black_50%,transparent)] pointer-events-none z-[11]"
	></div>

	<div
		class="absolute bottom-0 inset-x-0 pt-16 pb-4 px-4 flex flex-col justify-end z-[12]"
	>
		<h3 class="font-outfit font-bold text-white line-clamp-2">
			{book.title}
		</h3>
		{#if book.author}
			<p class="font-outfit text-sm text-stone-300 mt-1 line-clamp-1">
				{book.author}
			</p>
		{/if}
	</div>
{/snippet}

{#if isComingSoon}
	<div
		class="group relative aspect-[3/4] w-48 sm:w-56 rounded-2xl overflow-hidden shadow-lg transition-all duration-500 hover:-translate-y-2 hover:shadow-[0_20px_40px_-15px_rgba(124,58,237,0.4)] cursor-not-allowed"
		onmouseenter={() => (hovering = true)}
		onmouseleave={() => (hovering = false)}
		role="img"
		aria-label="{book.title} — coming soon"
	>
		<div
			class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105 z-10 grayscale-[30%] opacity-80"
		>
			<BookCardVideo
				src={book.cover_video_url}
				{hovering}
				fallbackChar={book.title.charAt(0)}
			/>
		</div>

		<div class="absolute top-3 right-3 z-20">
			<span
				class="px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase bg-accent text-white shadow-lg shadow-accent/20"
			>
				Coming Soon
			</span>
		</div>

		{@render cardContent()}
	</div>
{:else}
	<a
		href="/book/{book.book_id}"
		class="group block relative aspect-[3/4] w-48 sm:w-56 rounded-2xl overflow-hidden shadow-lg transition-all duration-500 hover:-translate-y-2 hover:shadow-[0_20px_40px_-15px_rgba(124,58,237,0.4)]"
		onmouseenter={() => (hovering = true)}
		onmouseleave={() => (hovering = false)}
	>
		<div
			class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105 z-10"
		>
			<BookCardVideo
				src={book.cover_video_url}
				{hovering}
				fallbackChar={book.title.charAt(0)}
			/>
		</div>

		{@render cardContent()}
	</a>
{/if}
