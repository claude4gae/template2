// 앱스토어 앱 등록/수정 다이얼로그
import { useEffect, useMemo, useRef, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectSeparator, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"

const MAX_CATEGORY_LENGTH = 100

function getClipboardImageFiles(clipboardData) {
  const items = Array.from(clipboardData?.items ?? [])
  return items
    .filter((item) => item.kind === "file" && item.type?.startsWith("image/"))
    .map((item) => item.getAsFile())
    .filter(Boolean)
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(typeof reader.result === "string" ? reader.result : "")
    reader.onerror = () => reject(reader.error || new Error("Failed to read file"))
    reader.readAsDataURL(file)
  })
}

export function AppFormDialog({
  open,
  onOpenChange,
  onSubmit,
  initialData,
  isSubmitting,
  categoryOptions = [],
  defaultContactName = "",
  defaultContactKnoxid = "",
}) {
  const [name, setName] = useState("")
  const [category, setCategory] = useState("")
  const [isCategorySelectOpen, setIsCategorySelectOpen] = useState(false)
  const [isAddingCategory, setIsAddingCategory] = useState(false)
  const [newCategoryName, setNewCategoryName] = useState("")
  const [url, setUrl] = useState("")
  const [manualUrl, setManualUrl] = useState("")
  const [description, setDescription] = useState("")
  const [contactName, setContactName] = useState("")
  const [contactKnoxid, setContactKnoxid] = useState("")
  const [screenshotUrls, setScreenshotUrls] = useState([])
  const [coverScreenshotIndex, setCoverScreenshotIndex] = useState(0)
  const [screenshotError, setScreenshotError] = useState("")
  const newCategoryInputRef = useRef(null)

  useEffect(() => {
    if (!open) return
    setIsCategorySelectOpen(false)
    setIsAddingCategory(false)
    setNewCategoryName("")
    if (initialData) {
      setName(initialData.name || "")
      setCategory(initialData.category || "")
      setUrl(initialData.url || "")
      setManualUrl(initialData.manualUrl || "")
      setDescription(initialData.description || "")
      setContactName(initialData.contactName || "")
      setContactKnoxid(initialData.contactKnoxid || "")
      const urls = Array.isArray(initialData.screenshotUrls)
        ? initialData.screenshotUrls.filter((value) => typeof value === "string" && value.trim())
        : []
      const resolvedUrls =
        urls.length > 0
          ? urls
          : typeof initialData.screenshotUrl === "string" && initialData.screenshotUrl.trim()
            ? [initialData.screenshotUrl.trim()]
            : []
      const coverIndexRaw = initialData.coverScreenshotIndex ?? 0
      const coverIndex = Number.isFinite(Number(coverIndexRaw)) ? Number(coverIndexRaw) : 0
      setScreenshotUrls(resolvedUrls)
      setCoverScreenshotIndex(
        Number.isInteger(coverIndex) && coverIndex >= 0 && coverIndex < resolvedUrls.length ? coverIndex : 0,
      )
      setScreenshotError("")
    } else {
      setName("")
      setCategory("")
      setUrl("")
      setManualUrl("")
      setDescription("")
      setContactName("")
      setContactKnoxid("")
      setScreenshotUrls([])
      setCoverScreenshotIndex(0)
      setScreenshotError("")
    }
  }, [initialData, open])

  useEffect(() => {
    if (!open || initialData) return
    setContactName((prev) => (prev ? prev : defaultContactName || ""))
    setContactKnoxid((prev) => (prev ? prev : defaultContactKnoxid || ""))
  }, [defaultContactName, defaultContactKnoxid, initialData, open])

  useEffect(() => {
    if (!isAddingCategory || !isCategorySelectOpen) return undefined
    const frameId = requestAnimationFrame(() => {
      newCategoryInputRef.current?.focus()
    })
    return () => cancelAnimationFrame(frameId)
  }, [isAddingCategory, isCategorySelectOpen])

  const title = useMemo(
    () => (initialData ? "앱 정보 수정" : "새 앱 등록"),
    [initialData],
  )
  const normalizedCategoryOptions = useMemo(() => {
    const unique = new Set()
    categoryOptions.forEach((option) => {
      if (typeof option !== "string") return
      const trimmed = option.trim()
      if (trimmed) unique.add(trimmed)
    })
    const currentCategory = initialData?.category
    if (typeof currentCategory === "string" && currentCategory.trim()) {
      unique.add(currentCategory.trim())
    }
    return Array.from(unique)
  }, [categoryOptions, initialData])
  const categorySelectOptions = useMemo(() => {
    const unique = new Set(normalizedCategoryOptions)
    const trimmedCategory = category.trim()
    if (trimmedCategory) unique.add(trimmedCategory)
    return Array.from(unique)
  }, [category, normalizedCategoryOptions])
  const selectedCategoryOption = categorySelectOptions.includes(category.trim()) ? category.trim() : ""

  const handleCategorySelectOpenChange = (nextOpen) => {
    setIsCategorySelectOpen(nextOpen)
    if (nextOpen) return
    setIsAddingCategory(false)
    setNewCategoryName("")
  }

  const handleCategorySelect = (value) => {
    setCategory(value)
    setIsAddingCategory(false)
    setNewCategoryName("")
    setIsCategorySelectOpen(false)
  }

  const handleAddCategory = () => {
    const nextCategory = newCategoryName.trim()
    if (!nextCategory) return
    setCategory(nextCategory)
    setIsAddingCategory(false)
    setNewCategoryName("")
    setIsCategorySelectOpen(false)
  }

  const handleSubmit = async () => {
    if (!name.trim() || !category.trim() || !url.trim()) return
    const normalizedScreenshotUrls = screenshotUrls
      .filter((value) => typeof value === "string")
      .map((value) => value.trim())
      .filter(Boolean)
    const normalizedCoverIndex =
      Number.isInteger(coverScreenshotIndex) &&
        coverScreenshotIndex >= 0 &&
        coverScreenshotIndex < normalizedScreenshotUrls.length
        ? coverScreenshotIndex
        : 0
    const payload = {
      name: name.trim(),
      category: category.trim(),
      url: url.trim(),
      manualUrl: manualUrl.trim(),
      description: description.trim(),
      contactName: contactName.trim(),
      contactKnoxid: contactKnoxid.trim(),
      screenshotUrl: normalizedScreenshotUrls[normalizedCoverIndex] || "",
      screenshotUrls: normalizedScreenshotUrls,
      coverScreenshotIndex: normalizedCoverIndex,
    }
    await onSubmit(payload)
  }

  const handleScreenshotPaste = async (event) => {
    const files = getClipboardImageFiles(event.clipboardData)
    if (!files.length) {
      setScreenshotError("이미지(스크린샷)만 붙여넣을 수 있어요.")
      return
    }

    event.preventDefault()
    setScreenshotError("")

    try {
      const dataUrls = await Promise.all(files.map((file) => fileToDataUrl(file)))
      const nextUrls = dataUrls.filter(Boolean)
      setScreenshotUrls((prev) => [...prev, ...nextUrls])
    } catch {
      setScreenshotError("스크린샷을 읽지 못했습니다. 다시 시도해 주세요.")
    }
  }

  const coverSrc = screenshotUrls[coverScreenshotIndex] || ""

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription className="sr-only">앱 정보를 입력하거나 수정합니다.</DialogDescription>
        </DialogHeader>

        <div className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="app-name">앱 이름</Label>
            <Input
              id="app-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="예: Slack Platform"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor={isAddingCategory ? "app-category-new" : "app-category-select"}>카테고리</Label>
            <Select
              open={isCategorySelectOpen}
              onOpenChange={handleCategorySelectOpenChange}
              value={selectedCategoryOption}
              onValueChange={handleCategorySelect}
            >
              <SelectTrigger id="app-category-select" aria-label="기존 카테고리 선택" className="w-full">
                <SelectValue placeholder={categorySelectOptions.length ? "기존 카테고리 선택" : "기존 카테고리 없음"} />
              </SelectTrigger>
              <SelectContent>
                {categorySelectOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
                {categorySelectOptions.length > 0 ? <SelectSeparator /> : null}
                {isAddingCategory ? (
                  <div
                    className="grid gap-2 p-2"
                    onPointerDownCapture={(event) => event.stopPropagation()}
                  >
                    <div className="flex items-center gap-2">
                      <Input
                        id="app-category-new"
                        ref={newCategoryInputRef}
                        value={newCategoryName}
                        onChange={(event) => setNewCategoryName(event.target.value)}
                        onKeyDown={(event) => {
                          event.stopPropagation()
                          if (event.key === "Enter") {
                            event.preventDefault()
                            handleAddCategory()
                          }
                          if (event.key === "Escape") {
                            event.preventDefault()
                            setIsAddingCategory(false)
                            setNewCategoryName("")
                          }
                        }}
                        placeholder="새 카테고리 입력"
                        maxLength={MAX_CATEGORY_LENGTH}
                        className="h-8"
                        autoFocus
                      />
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={handleAddCategory}
                        disabled={!newCategoryName.trim()}
                        className="h-8 shrink-0"
                      >
                        추가
                      </Button>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setIsAddingCategory(false)
                        setNewCategoryName("")
                      }}
                      className="h-7 justify-start px-2 text-xs text-muted-foreground"
                    >
                      취소
                    </Button>
                  </div>
                ) : (
                  <button
                    type="button"
                    className="relative flex w-full cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm text-muted-foreground outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground"
                    onPointerDown={(event) => {
                      event.preventDefault()
                      event.stopPropagation()
                      setIsAddingCategory(true)
                      setNewCategoryName("")
                      setIsCategorySelectOpen(true)
                    }}
                    onKeyDown={(event) => {
                      if (event.key !== "Enter" && event.key !== " ") return
                      event.preventDefault()
                      event.stopPropagation()
                      setIsAddingCategory(true)
                      setNewCategoryName("")
                      setIsCategorySelectOpen(true)
                    }}
                  >
                    + 새 카테고리 추가
                  </button>
                )}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="app-url">URL</Label>
            <Input
              id="app-url"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://example.com"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="app-manual-url">Manual URL</Label>
            <Input
              id="app-manual-url"
              value={manualUrl}
              onChange={(event) => setManualUrl(event.target.value)}
              placeholder="https://example.com/manual"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="app-description">설명</Label>
            <textarea
              id="app-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="앱의 주요 기능과 사용 목적을 입력하세요."
              className="min-h-[140px] w-full resize-none rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
            />
          </div>

          <div className="grid gap-2 sm:grid-cols-2 sm:gap-3">
            <div className="grid gap-2 sm:col-span-2">
              <Label id="app-screenshot-label">스크린샷 (여러 장 붙여넣기)</Label>
              <div className="grid gap-2">
                <div
                  id="app-screenshot"
                  aria-labelledby="app-screenshot-label"
                  tabIndex={0}
                  onPaste={handleScreenshotPaste}
                  className="grid min-h-[140px] place-items-center rounded-md border bg-muted/40 p-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
                >
                  {coverSrc ? (
                    <img
                      src={coverSrc}
                      alt="대표 스크린샷 미리보기"
                      className="max-h-56 w-full rounded-md object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <div className="grid gap-2 text-center">
                      <p className="text-sm font-medium text-foreground">여기에 스크린샷을 붙여넣어 주세요</p>
                      <p className="text-xs text-muted-foreground">Ctrl+V / ⌘V</p>
                    </div>
                  )}
                </div>

                {screenshotError ? (
                  <p className="text-xs text-destructive">{screenshotError}</p>
                ) : null}

                {screenshotUrls.length ? (
                  <div className="grid grid-cols-3 gap-2">
                    {screenshotUrls.map((src, index) => {
                      const isCover = index === coverScreenshotIndex
                      return (
                        <div key={`${index}-${src.slice(0, 24)}`} className="grid gap-1">
                          <button
                            type="button"
                            onClick={() => setCoverScreenshotIndex(index)}
                            className={cn(
                              "relative overflow-hidden rounded-md border bg-muted/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30",
                              isCover && "ring-2 ring-primary/40",
                            )}
                          >
                            <img
                              src={src}
                              alt={`스크린샷 ${index + 1}`}
                              className="h-20 w-full object-cover"
                              loading="lazy"
                            />
                            {isCover ? (
                              <div className="absolute left-1 top-1 rounded bg-primary px-1.5 py-0.5 text-[10px] font-medium text-primary-foreground">
                                대표
                              </div>
                            ) : null}
                          </button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 px-2 text-xs"
                            onClick={() => {
                              setScreenshotUrls((prev) => prev.filter((_, i) => i !== index))
                              setCoverScreenshotIndex((prevIndex) => {
                                if (index === prevIndex) return 0
                                if (index < prevIndex) return Math.max(prevIndex - 1, 0)
                                return prevIndex
                              })
                            }}
                            type="button"
                          >
                            삭제
                          </Button>
                        </div>
                      )
                    })}
                  </div>
                ) : null}

                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs text-muted-foreground">
                    {screenshotUrls.length
                      ? `${screenshotUrls.length}장 등록됨 · 대표 이미지를 선택하세요.`
                      : "클릭 후 붙여넣기(Ctrl+V)를 사용하세요."}
                  </p>
                  {screenshotUrls.length ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setScreenshotUrls([])
                        setCoverScreenshotIndex(0)
                        setScreenshotError("")
                      }}
                      type="button"
                    >
                      전체 삭제
                    </Button>
                  ) : null}
                </div>
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="app-contact-name">담당자 이름</Label>
              <Input
                id="app-contact-name"
                value={contactName}
                onChange={(event) => setContactName(event.target.value)}
                placeholder="홍길동"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="app-contact-knoxid">담당자 Knox ID</Label>
              <Input
                id="app-contact-knoxid"
                value={contactKnoxid}
                onChange={(event) => setContactKnoxid(event.target.value)}
                placeholder="이메일 @ 앞부분"
              />
            </div>
          </div>
        </div>

        <DialogFooter className="pt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)} type="button">
            취소
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting || !name || !category || !url} type="button">
            {initialData ? "수정 완료" : "등록"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
