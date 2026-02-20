<script lang="ts">
    // We will use this fake state to build the UI.
    // Later, you will pass this in as an export let volume = 1;
    let volume = 0.75;
    let isHovered = false;

    // We'll change the icon based on how loud it is
    $: isMuted = volume === 0;
    $: isLow = volume > 0 && volume < 0.5;
</script>

<div
    role="group"
    aria-label="Volume controls"
    class="group relative flex items-center h-12"
    onmouseenter={() => (isHovered = true)}
    onmouseleave={() => (isHovered = false)}
>
    <button
        class="w-12 h-12 flex items-center justify-center text-muted hover:text-text transition-colors"
    >
        {#if isMuted}
            <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.5"
                stroke="currentColor"
                class="w-5 h-5"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M17.25 9.75L19.5 12m0 0l2.25 2.25M19.5 12l2.25-2.25M19.5 12l-2.25 2.25m-10.5-6l4.72-4.72a.75.75 0 011.28.531V19.69a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.506-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"
                />
            </svg>
        {:else if isLow}
            <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.5"
                stroke="currentColor"
                class="w-5 h-5"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M11.25 19.5l-4.72-4.72H4.51c-.88 0-1.704-.506-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75l4.72-4.72a.75.75 0 011.28.531V19.69a.75.75 0 01-1.28.53z"
                />
            </svg>
        {:else}
            <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.5"
                stroke="currentColor"
                class="w-5 h-5"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.531V19.69a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.506-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"
                />
            </svg>
        {/if}
    </button>

    <div
        class="overflow-hidden transition-all duration-300 ease-out flex items-center {isHovered
            ? 'w-24 opacity-100 pr-2'
            : 'w-0 opacity-0'}"
    >
        <div
            class="relative w-full h-1.5 bg-black/10 dark:bg-white/10 rounded-full cursor-pointer"
        >
            <div
                class="absolute left-0 top-0 h-full bg-accent rounded-full transition-all duration-100"
                style="width: {volume * 100}%"
            ></div>
            <div
                class="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-sm border border-black/5 dark:border-white/10 opacity-0 group-hover:opacity-100 transition-opacity"
                style="left: calc({volume * 100}% - 6px)"
            ></div>
        </div>
    </div>
</div>
