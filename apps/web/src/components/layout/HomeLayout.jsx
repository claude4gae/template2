// 파일 경로: src/components/layout/HomeLayout.jsx
import { ContentLayout } from "./ContentLayout"

export function HomeLayout({
  children,
  contentMaxWidthClass = "max-w-10xl",
  scrollAreaClassName = "overflow-y-auto",
  paddingClassName = "px-4 pb-3",
  innerClassName = "mx-auto flex h-full w-full flex-col gap-4",
}) {
  return (
    <div className="h-full flex flex-col bg-background">
      <main className="flex-1 min-h-0 min-w-0 overflow-hidden">
        <ContentLayout
          contentMaxWidthClass={contentMaxWidthClass}
          scrollAreaClassName={scrollAreaClassName}
          paddingClassName={paddingClassName}
          innerClassName={innerClassName}
        >
          {children}
        </ContentLayout>
      </main>
    </div>
  )
}
