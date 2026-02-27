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
		class="absolute bottom-0 inset-x-0 h-2/3 bg-gradient-to-t from-black/80 via-black/40 to-transparent pointer-events-none z-[11]"
	></div>

	<div
		class="absolute bottom-0 inset-x-0 pt-20 pb-5 px-5 flex flex-col justify-end z-[12]"
	>
		<h3 class="font-display text-xl font-medium text-white leading-snug line-clamp-2 tracking-tight">
			{book.title}
		</h3>
		{#if book.author}
			<p class="text-xs text-white/50 mt-1 line-clamp-1 tracking-wider uppercase font-medium">
				{book.author}
			</p>
		{/if}
	</div>
{/snippet}

{#if isComingSoon}
	<div
		class="group relative aspect-[3/4] w-52 sm:w-60 rounded-2xl overflow-hidden shadow-lg shadow-black/15 dark:shadow-black/40 transition-all duration-700 ease-out hover:-translate-y-1 hover:shadow-xl cursor-not-allowed"
		onmouseenter={() => (hovering = true)}
		onmouseleave={() => (hovering = false)}
		role="img"
		aria-label="{book.title} — coming soon"
	>
		<div
			class="absolute inset-0 w-full h-full object-cover transition-transform duration-[900ms] ease-out group-hover:scale-[1.04] z-10 grayscale-[30%] opacity-70"
		>
			<BookCardVideo
				src={book.cover_video_url}
				{hovering}
				fallbackChar={book.title.charAt(0)}
			/>
		</div>

		<div class="absolute top-3.5 right-3.5 z-20">
			<span
				class="px-3 py-1 rounded-full text-[8px] font-bold tracking-[0.15em] uppercase bg-text/80 text-background backdrop-blur-sm"
			>
				Coming Soon
			</span>
		</div>

		{@render cardContent()}
	</div>
{:else}
	<a
		href="/book/{book.book_id}"
		class="group block relative aspect-[3/4] w-52 sm:w-60 rounded-2xl overflow-hidden shadow-lg shadow-black/15 dark:shadow-black/40 transition-all duration-700 ease-out hover:-translate-y-2 hover:shadow-2xl hover:shadow-accent/20 dark:hover:shadow-accent/10"
		onmouseenter={() => (hovering = true)}
		onmouseleave={() => (hovering = false)}
	>
		<div
			class="absolute inset-0 w-full h-full object-cover transition-transform duration-[900ms] ease-out group-hover:scale-[1.05] z-10"
		>
			<BookCardVideo
				src={book.cover_video_url}
				{hovering}
				fallbackChar={book.title.charAt(0)}
			/>
		</div>

		<!-- Hover glow ring -->
		<div class="absolute inset-0 z-[13] rounded-2xl ring-1 ring-inset ring-white/[0.08] opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

		{@render cardContent()}
	</a>
{/if}
