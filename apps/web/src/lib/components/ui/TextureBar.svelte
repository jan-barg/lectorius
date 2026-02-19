<div class="relative w-full my-8 flex items-center justify-center opacity-80" role="presentation">

  <div
    class="
      absolute w-full h-[4px] rounded-full
      bg-gradient-to-r from-transparent via-violet-500/50 to-transparent
      blur-[1px]
      dark:via-violet-500/40
    "
    style="filter: url(#paper-grain);"
  ></div>

  <div
    class="
      relative w-full h-[1.5px] rounded-full
      bg-gradient-to-r from-transparent via-violet-600 to-transparent
      shadow-[0_0_10px_rgba(124,58,237,0.3)]
      dark:shadow-[0_0_15px_rgba(124,58,237,0.6)]
      opacity-90
      animate-pulse-slow
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
  @keyframes pulse-slow {
    0%, 100% { opacity: 0.8; transform: scaleX(0.98); }
    50% { opacity: 1; transform: scaleX(1); }
  }
  .animate-pulse-slow {
    animation: pulse-slow 4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
</style>
