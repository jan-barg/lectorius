<div class="relative w-full my-8 py-2 flex items-center justify-center" role="presentation">

  <div
    class="
      absolute w-[80%] h-2 rounded-full
      bg-gradient-to-r from-transparent via-violet-500/40 to-transparent
      blur-md
      dark:via-violet-500/30
      animate-texture-breathe
    "
  ></div>

  <div
    class="
      absolute w-[90%] h-1.5 rounded-full
      bg-gradient-to-r from-transparent via-violet-600/60 to-transparent
      opacity-70 mix-blend-multiply dark:mix-blend-screen
    "
    style="filter: url(#paper-grain);"
  ></div>

  <div
    class="
      relative w-full h-0.5 rounded-full
      bg-gradient-to-r from-transparent via-violet-600 to-transparent
      opacity-90
    "
  ></div>

  <svg class="absolute w-0 h-0" aria-hidden="true">
    <filter id="paper-grain">
      <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" stitchTiles="stitch" result="noise"/>
      <feColorMatrix type="saturate" values="0" in="noise"/>
      <feComponentTransfer>
        <feFuncA type="linear" slope="0.4" />
      </feComponentTransfer>
      <feComposite operator="in" in2="SourceGraphic" />
    </filter>
  </svg>
</div>

<style>
  /* A very slow, calming breath animation */
  @keyframes texture-breathe {
    0%, 100% { opacity: 0.4; transform: scaleX(0.95); }
    50% { opacity: 0.8; transform: scaleX(1.05); }
  }
  .animate-texture-breathe {
    animation: texture-breathe 6s ease-in-out infinite;
  }
</style>
