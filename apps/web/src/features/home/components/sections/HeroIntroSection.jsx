import { Badge } from "@/components/ui/badge"

export function HeroIntroSection() {
  return (
    <div className="flex flex-col items-center gap-5 text-center">
      <Badge variant="outline" className="text-sm font-normal">
        메모리Etch기술팀
      </Badge>

      <h1 className="text-2xl font-semibold sm:text-3xl lg:text-6xl lg:font-bold">
        <span>Etch </span>
        <span className="shimmer-text">AI Transformation </span>
        <span> Portal</span>
      </h1>

      <p className="text-muted-foreground max-w-4xl text-md">
        데이터 연결과 업무 자동화를 통해{" "}
        <br className="max-lg:hidden" /> AI 기반의 빠르고 스마트한 Workflow을 제공합니다.
      </p>
    </div>
  )
}
