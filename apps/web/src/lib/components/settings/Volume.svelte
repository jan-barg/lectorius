<script lang="ts">
    import { playback } from '$lib/stores/playback';
    import { onDestroy } from 'svelte';

    let volume = 1;
    let preMuteVolume = 1;
    let isHovered = false;
    let isDragging = false;
    let trackEl: HTMLDivElement;

    const unsub = playback.subscribe((s) => {
        volume = s.volume;
    });

    $: isMuted = volume === 0;
    $: isLow = volume > 0 && volume < 0.5;

    function toggleMute() {
        if (isMuted) {
            playback.setVolume(preMuteVolume || 0.75);
        } else {
            preMuteVolume = volume;
            playback.setVolume(0);
        }
    }

    function volumeFromPointer(e: PointerEvent) {
        const rect = trackEl.getBoundingClientRect();
        const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        playback.setVolume(ratio);
    }

    function handleTrackPointerDown(e: PointerEvent) {
        isDragging = true;
        volumeFromPointer(e);
        window.addEventListener('pointermove', handleWindowPointerMove);
        window.addEventListener('pointerup', handleWindowPointerUp);
    }

    function handleWindowPointerMove(e: PointerEvent) {
        if (!isDragging) return;
        volumeFromPointer(e);
    }

    function handleWindowPointerUp() {
        isDragging = false;
        window.removeEventListener('pointermove', handleWindowPointerMove);
        window.removeEventListener('pointerup', handleWindowPointerUp);
    }

    onDestroy(() => {
        unsub();
        window.removeEventListener('pointermove', handleWindowPointerMove);
        window.removeEventListener('pointerup', handleWindowPointerUp);
    });
</script>

<div
    role="group"
    aria-label="Volume controls"
    class="group relative flex items-center h-11"
    onmouseenter={() => (isHovered = true)}
    onmouseleave={() => { if (!isDragging) isHovered = false; }}
>
    <button
        onclick={toggleMute}
        class="w-11 h-11 flex items-center justify-center rounded-xl text-muted hover:text-text hover:bg-text/[0.04] dark:hover:bg-white/[0.04] transition-all duration-300"
        aria-label={isMuted ? 'Unmute' : 'Mute'}
    >
        {#if isMuted}
            <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.5"
                stroke="currentColor"
                class="w-[18px] h-[18px]"
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
                class="w-[18px] h-[18px]"
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
                class="w-[18px] h-[18px]"
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
        class="overflow-hidden transition-all duration-300 ease-out flex items-center {isHovered || isDragging
            ? 'w-24 opacity-100 pr-2'
            : 'w-0 opacity-0'}"
    >
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
            bind:this={trackEl}
            class="relative w-full h-[3px] bg-text/[0.08] dark:bg-white/[0.08] rounded-full cursor-pointer"
            onpointerdown={handleTrackPointerDown}
        >
            <div
                class="absolute left-0 top-0 h-full bg-accent rounded-full transition-[width] duration-100"
                style="width: {volume * 100}%"
            ></div>
            <div
                class="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 bg-accent rounded-full shadow-md shadow-accent/25 opacity-0 group-hover:opacity-100 transition-all duration-300"
                style="left: calc({volume * 100}% - 5px)"
            ></div>
        </div>
    </div>
</div>
