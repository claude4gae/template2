import { forwardRef } from "react"

export const HeroVideoCard = forwardRef(function HeroVideoCard(
  { videoSrc },
  ref,
) {
  return (
    <div
      ref={ref}
      className="bg-background relative z-20 flex items-center justify-center rounded-xl border p-2"
    >
      <div className="bg-secondary relative flex h-50 w-50 items-center justify-center overflow-hidden rounded-xl border-[1.5px] shadow-xl">
        <video
          className="aspect-video h-full w-full object-cover"
          src={videoSrc}
          autoPlay
          loop
          muted
          playsInline
        />
      </div>
    </div>
  )
})
