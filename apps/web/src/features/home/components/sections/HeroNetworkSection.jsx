import { useRef } from "react"
import {
  BotMessageSquareIcon,
  ChartSpline,
  Cloud,
  CodeXmlIcon,
  Cpu,
  DatabaseIcon,
  HeartHandshake,
  Puzzle,
  ThumbsUp,
} from "lucide-react"

import { HeroIconNodeCard } from "../cards/HeroIconNodeCard"
import { HeroValuePillarCard } from "../cards/HeroValuePillarCard"
import { HeroVideoCard } from "../cards/HeroVideoCard"
import { StraightBeam } from "../StraightBeam"

const BEAM_DURATION = 4.5
const BEAM_COLOR = "var(--primary)"

const HERO_VALUES = [
  { label: "사람존중", icon: HeartHandshake },
  { label: "다름의인정", icon: Puzzle },
  { label: "Value Up", icon: ThumbsUp },
]

export function HeroNetworkSection({ videoSrc }) {
  const containerRef = useRef(null)
  const codeIconRef = useRef(null)
  const botIconRef = useRef(null)
  const databaseIconRef = useRef(null)
  const videoRef = useRef(null)
  const chartIconRef = useRef(null)
  const cloudIconRef = useRef(null)
  const cpuIconRef = useRef(null)
  const spanRef1 = useRef(null)
  const spanRef2 = useRef(null)
  const spanRef3 = useRef(null)
  const spanRef4 = useRef(null)
  const spanRef5 = useRef(null)
  const spanRef6 = useRef(null)
  const spanRef7 = useRef(null)
  const spanRef8 = useRef(null)

  const desktopBeams = [
    { key: "code-span-1", fromRef: codeIconRef, toRef: spanRef1 },
    { key: "span-1-span-3", fromRef: spanRef1, toRef: spanRef3 },
    { key: "bot-span-2", fromRef: botIconRef, toRef: spanRef2 },
    { key: "span-2-span-6", fromRef: spanRef2, toRef: spanRef6 },
    { key: "cloud-span-7", fromRef: cloudIconRef, toRef: spanRef7 },
    { key: "span-7-span-4", fromRef: spanRef7, toRef: spanRef4 },
    { key: "cpu-span-8", fromRef: cpuIconRef, toRef: spanRef8 },
    { key: "span-8-span-5", fromRef: spanRef8, toRef: spanRef5 },
    { key: "database-span-3", fromRef: databaseIconRef, toRef: spanRef3 },
    { key: "span-3-span-4", fromRef: spanRef3, toRef: spanRef4 },
    { key: "span-4-video", fromRef: spanRef4, toRef: videoRef },
    { key: "video-span-5", fromRef: videoRef, toRef: spanRef5 },
    { key: "span-5-span-6", fromRef: spanRef5, toRef: spanRef6 },
    { key: "span-6-chart", fromRef: spanRef6, toRef: chartIconRef },
  ]
  const mobileBeams = [
    { key: "mobile-database-video", fromRef: databaseIconRef, toRef: videoRef },
    { key: "mobile-video-chart", fromRef: videoRef, toRef: chartIconRef },
  ]

  const renderBeam = ({ key, fromRef, toRef }, className) => (
    <StraightBeam
      key={key}
      containerRef={containerRef}
      fromRef={fromRef}
      toRef={toRef}
      gradientStartColor={BEAM_COLOR}
      duration={BEAM_DURATION}
      className={className}
    />
  )

  return (
    <div ref={containerRef} className="relative flex w-full flex-col items-center">
      <div className="flex h-18 w-full max-w-4xl items-start justify-between max-md:hidden">
        <div className="flex items-center gap-30">
          <HeroIconNodeCard
            ref={codeIconRef}
            icon={CodeXmlIcon}
            className="size-12 lg:size-15"
            iconClassName="size-7 lg:size-10"
          />
          <span ref={spanRef1} className="size-0.5 max-md:hidden" />
          <div className="flex flex-col items-center gap-4 text-xl font-semibold text-foreground">
            <div className="flex items-center gap-10 pl-7 text-lg font-semibold">
              {HERO_VALUES.map((value) => (
                <HeroValuePillarCard
                  key={value.label}
                  icon={value.icon}
                  label={value.label}
                />
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-30">
          <span ref={spanRef2} className="size-0.5 max-md:hidden" />
          <HeroIconNodeCard
            ref={botIconRef}
            icon={BotMessageSquareIcon}
            className="size-12 lg:size-15"
            iconClassName="size-7 lg:size-8"
          />
        </div>
      </div>

      <div className="flex w-full items-center justify-between py-2.5">
        <HeroIconNodeCard
          ref={databaseIconRef}
          icon={DatabaseIcon}
          className="size-15 shrink-0 shadow-xl md:size-18 lg:size-23"
          iconClassName="size-8 md:size-10 lg:size-13"
        />
        <div className="flex items-center justify-between md:w-full md:max-w-70 lg:max-w-100">
          <div className="flex w-full max-w-20 justify-between max-md:hidden">
            <span ref={spanRef3} className="size-0.5" />
            <span ref={spanRef4} className="size-0.5" />
          </div>
          <HeroVideoCard ref={videoRef} videoSrc={videoSrc} />
          <div className="flex w-full max-w-20 justify-between max-md:hidden">
            <span ref={spanRef5} className="size-0.5" />
            <span ref={spanRef6} className="size-0.5" />
          </div>
        </div>
        <HeroIconNodeCard
          ref={chartIconRef}
          icon={ChartSpline}
          className="size-15 shrink-0 shadow-xl md:size-18 lg:size-23"
          iconClassName="size-8 md:size-10 lg:size-13"
        />
      </div>

      <div className="flex h-18 w-full max-w-4xl items-center justify-between max-md:hidden">
        <div className="flex items-center gap-30">
          <HeroIconNodeCard
            ref={cloudIconRef}
            icon={Cloud}
            className="size-12 lg:size-15"
            iconClassName="size-6 lg:size-8"
          />
          <span ref={spanRef7} className="size-0.5 max-md:hidden" />
        </div>

        <div className="flex items-center gap-30">
          <span ref={spanRef8} className="size-0.5 max-md:hidden" />
          <HeroIconNodeCard
            ref={cpuIconRef}
            icon={Cpu}
            className="size-12 lg:size-15"
            iconClassName="size-7 lg:size-11"
          />
        </div>
      </div>

      {desktopBeams.map((beam) => renderBeam(beam, "max-md:hidden"))}
      {mobileBeams.map((beam) => renderBeam(beam, "md:hidden"))}
    </div>
  )
}
