<script lang="ts">
	import type { BookListItem } from "$lib/types";
	import BookCardVideo from "./BookCardVideo.svelte";
	import ProgressOverlay from "./ProgressOverlay.svelte";

	export let book: BookListItem;
	export let progress: number | null = null;

	let hovering = false;

	$: isComingSoon = book.status === "coming_soon";
</script>

{#snippet cardContent()}
	{#if progress !== null && !isComingSoon}
		<div class="absolute bottom-0 left-0 w-full z-[15]">
			<ProgressOverlay percentage={progress} />
		</div>
	{/if}

	<div
		class="absolute bottom-0 inset-x-0 h-1/2 bg-gradient-to-t from-black/70 via-black/30 to-transparent pointer-events-none z-[11]"
	></div>

	<div
		class="absolute bottom-0 inset-x-0 pt-16 pb-4 px-4 flex flex-col justify-end z-[12]"
	>
		<h3 class="font-display text-lg font-medium text-white leading-snug line-clamp-2">
			{book.title}
		</h3>
		{#if book.author}
			<p class="text-[13px] text-white/60 mt-0.5 line-clamp-1 tracking-wide">
				{book.author}
			</p>
		{/if}
	</div>
{/snippet}

{#if isComingSoon}
	<div
		class="group relative aspect-[3/4] w-44 sm:w-52 rounded-xl overflow-hidden shadow-md shadow-black/10 dark:shadow-black/30 transition-all duration-500 hover:-translate-y-1 hover:shadow-lg cursor-not-allowed"
		onmouseenter={() => (hovering = true)}
		onmouseleave={() => (hovering = false)}
		role="img"
		aria-label="{book.title} — coming soon"
	>
		<div
			class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-[1.03] z-10 grayscale-[30%] opacity-75"
		>
			<BookCardVideo
				src={book.cover_video_url}
				{hovering}
				fallbackChar={book.title.charAt(0)}
			/>
		</div>

		<div class="absolute top-3 right-3 z-20">
			<span
				class="px-2.5 py-1 rounded-full text-[9px] font-bold tracking-[0.12em] uppercase bg-text/80 text-background"
			>
				Coming Soon
			</span>
		</div>

		{@render cardContent()}
	</div>
{:else}
	<a
		href="/book/{book.book_id}"
		class="group block relative aspect-[3/4] w-44 sm:w-52 rounded-xl overflow-hidden shadow-md shadow-black/10 dark:shadow-black/30 transition-all duration-500 hover:-translate-y-1.5 hover:shadow-xl hover:shadow-accent/15"
		onmouseenter={() => (hovering = true)}
		onmouseleave={() => (hovering = false)}
	>
		<div
			class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-[1.03] z-10"
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
