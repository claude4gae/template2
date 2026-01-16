// 파일 경로: src/features/voc/pages/VocBoardPage.jsx
// VOC 게시판: 새 글 작성, 답변, 상태 관리, 권한 기반 삭제를 제공하는 클라이언트 사이드 UI
import * as React from "react"
import { useOutletContext } from "react-router-dom"
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Loader2,
  MessageSquare,
  Pencil,
  PlusCircle,
  RefreshCw,
  Reply,
  Trash2,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/common"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { APP_CATEGORIES, DEFAULT_APP_CATEGORY, STATUS_OPTIONS } from "../utils/constants"
import { RichTextEditor } from "../components/RichTextEditor"
import { formatTimestamp, sanitizeContentHtml, hasMeaningfulContent } from "../utils"
import "../utils/quill.css"
import "quill/dist/quill.snow.css"

// 리치 텍스트 에디터 설정: 모듈/포맷은 VOC 화면만을 위한 최소 구성이며, 필요 시 확장 가능
const QUILL_MODULES = {
  toolbar: [
    [{ header: [1, 2, 3, false] }],
    ["bold", "italic", "underline", "strike"],
    [{ color: [] }, { background: [] }],
    [{ list: "ordered" }, { list: "bullet" }],
    [{ align: [] }],
    ["link", "image"],
  ],
  clipboard: {
    matchVisual: false,
  },
}

const QUILL_FORMATS = [
  "header",
  "bold",
  "italic",
  "underline",
  "strike",
  "color",
  "background",
  "list",
  "bullet",
  "align",
  "link",
  "image",
]

function StatusBadge({ status }) {
  const tone = STATUS_OPTIONS.find((option) => option.value === status)?.tone
  return (
    <Badge className={["border", tone].filter(Boolean).join(" ")}>
      {status || "상태 미정"}
    </Badge>
  )
}

function PostContent({ content, className = "", allowResize = false }) {
  const safeHtml = React.useMemo(() => sanitizeContentHtml(content), [content])
  const containerClassName = [
    "overflow-x-auto overflow-y-auto rounded-md border border-input bg-muted/20 px-3 py-3 shadow-xs min-w-full max-w-full",
    className,
  ]
    .filter(Boolean)
    .join(" ")

  const bodyClassName = [
    "voc-post-body",
    allowResize ? "voc-post-body--resizable" : "",
  ]
    .filter(Boolean)
    .join(" ")

  return (
    <div className={containerClassName}>
      {safeHtml ? (
        <div className={bodyClassName} dangerouslySetInnerHTML={{ __html: safeHtml }} />
      ) : (
        <p className="text-sm text-muted-foreground">내용이 없습니다.</p>
      )}
    </div>
  )
}

export function VocBoardPage() {
  const {
    statusCounts,
    statusFilter,
    appFilter,
    isMyPostsOnly,
    filteredPosts,
    visiblePosts,
    pagination,
    selectedPost,
    clearSelection,
    isCreateOpen,
    setIsCreateOpen,
    isDetailOpen,
    setIsDetailOpen,
    replyDrafts,
    updateReplyDraft,
    form,
    updateForm,
    resetForm,
    createPost,
    deletePost,
    addReply,
    updateStatus,
    selectPost,
    toggleStatusFilter,
    toggleMyPostsOnly,
    changePageSize,
    nextPage,
    prevPage,
    firstPage,
    lastPage,
    canDeletePost,
    updatePost,
    isLoading,
    error,
    reload,
    isSubmitting,
    isUpdating,
    isRefreshing,
    isReplying,
  } = useOutletContext()

  const totalPosts = Object.values(statusCounts || {}).reduce(
    (sum, count) => sum + (Number.isFinite(count) ? count : 0),
    0,
  )
  const appFilterLabel = appFilter || "전체"

  const handleCreateOpenChange = (open) => {
    setIsCreateOpen(open)
    if (open) {
      updateForm("app", appFilter || form.app || DEFAULT_APP_CATEGORY)
    }
  }

  const handleCreatePost = React.useCallback(
    async (event) => {
      event.preventDefault()
      await createPost()
    },
    [createPost],
  )

  const [deleteTarget, setDeleteTarget] = React.useState(null)
  const [isEditing, setIsEditing] = React.useState(false)
  const [editForm, setEditForm] = React.useState({ title: "", content: "" })

  const handleDetailOpenChange = React.useCallback(
    (open) => {
      setIsDetailOpen(open)
      if (!open) {
        clearSelection()
        setIsEditing(false)
      }
    },
    [clearSelection, setIsDetailOpen],
  )

  React.useEffect(() => {
    if (selectedPost) {
      setEditForm({
        title: selectedPost.title || "",
        content: selectedPost.content || "",
      })
      setIsEditing(false)
    } else {
      setEditForm({ title: "", content: "" })
      setIsEditing(false)
    }
  }, [selectedPost])

  const handleRequestDelete = React.useCallback((post) => {
    if (!post) return
    setDeleteTarget({ id: post.id, title: post.title })
  }, [])

  const handleDeleteDialogOpenChange = React.useCallback((open) => {
    if (!open) setDeleteTarget(null)
  }, [])

  const handleConfirmDelete = React.useCallback(() => {
    if (!deleteTarget?.id) return
    deletePost(deleteTarget.id)
    setDeleteTarget(null)
  }, [deletePost, deleteTarget])

  const clearStatusFilter = React.useCallback(() => {
    if (statusFilter) {
      toggleStatusFilter(statusFilter)
    }
  }, [statusFilter, toggleStatusFilter])

  const sanitizedDraft = React.useMemo(
    () => sanitizeContentHtml(form.content),
    [form.content],
  )

  const hasDraftContent = React.useMemo(
    () => hasMeaningfulContent(sanitizedDraft, { skipSanitize: true }),
    [sanitizedDraft],
  )

  const isSubmitDisabled =
    isSubmitting || !form.title.trim() || !form.app?.trim() || !hasDraftContent
  const canEditSelected = selectedPost ? canDeletePost(selectedPost) : false
  const replyDraftValue = selectedPost ? replyDrafts[selectedPost.id] || "" : ""
  const isReplyDisabled = !replyDraftValue.trim() || isReplying

  const handleSaveEdit = React.useCallback(async () => {
    if (!selectedPost) return
    const updated = await updatePost(selectedPost.id, {
      title: editForm.title,
      content: editForm.content,
    })
    if (updated) {
      setIsEditing(false)
    }
  }, [editForm.content, editForm.title, selectedPost, updatePost])

  const handleCancelEdit = React.useCallback(() => {
    if (!selectedPost) {
      setIsEditing(false)
      setEditForm({ title: "", content: "" })
      return
    }
    setEditForm({ title: selectedPost.title || "", content: selectedPost.content || "" })
    setIsEditing(false)
  }, [selectedPost])

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col gap-3 overflow-hidden">
      <Card className="flex-shrink-0">
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-3">

              <CardDescription className="text-sm text-muted-foreground">
                VOC를 남겨 주시면 빠르게 답변드리겠습니다.
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <span className="rounded-full bg-muted px-2 py-1 text-foreground shadow-xs">
                총 {totalPosts}건의 문의
              </span>
              <span className="rounded-full bg-muted px-2 py-1 text-foreground shadow-xs">
                앱 {appFilterLabel}
              </span>
              {isRefreshing ? (
                <span className="inline-flex items-center gap-1 text-primary">
                  <Loader2 className="size-3 animate-spin" aria-hidden="true" />
                  최신 상태로 동기화 중
                </span>
              ) : null}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 self-start sm:ml-auto">
            <Button
              variant="outline"
              size="icon"
              onClick={() => reload()}
              disabled={isLoading || isRefreshing}
              aria-label="VOC 게시판 새로고침"
              title="새로고침"
            >
              {isRefreshing ? (
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              ) : (
                <RefreshCw className="size-4" aria-hidden="true" />
              )}
            </Button>
            <Dialog open={isCreateOpen} onOpenChange={handleCreateOpenChange}>
              <DialogTrigger asChild>
                <Button className="self-start sm:ml-auto">
                  <PlusCircle className="size-4" aria-hidden="true" />
                  새 글 작성
                </Button>
              </DialogTrigger>
              <DialogContent className="w-[min(1100px,calc(100%-2rem))] min-w-[min(1100px,calc(100%-2rem))] max-w-[min(1100px,calc(100%-2rem))] h-[80vh] min-h-[80vh] max-h-[80vh] overflow-y-auto overflow-x-hidden">
                <DialogHeader>
                  <DialogTitle>새 글 작성</DialogTitle>
                  <DialogDescription className="sr-only">VOC 게시판 새 글을 작성합니다.</DialogDescription>
                </DialogHeader>
                <form className="space-y-4" onSubmit={handleCreatePost}>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground" htmlFor="voc-app">
                      앱 카테고리
                    </label>
                    <select
                      id="voc-app"
                      value={form.app}
                      onChange={(event) => updateForm("app", event.target.value)}
                      className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground shadow-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
                      required
                    >
                      {APP_CATEGORIES.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground" htmlFor="voc-title">
                      제목
                    </label>
                    <Input
                      id="voc-title"
                      value={form.title}
                      onChange={(event) => updateForm("title", event.target.value)}
                      placeholder="무엇을 도와드릴까요?"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <label
                      className="text-sm font-medium text-foreground"
                      id="voc-content-label"
                      htmlFor="voc-content-editor"
                    >
                      내용
                    </label>
                    <RichTextEditor
                      id="voc-content-editor"
                      value={form.content}
                      onChange={(value) => updateForm("content", value)}
                      modules={QUILL_MODULES}
                      formats={QUILL_FORMATS}
                      placeholder="상세한 내용을 적어 주세요."
                      ariaLabelledby="voc-content-label"
                    />
                  </div>

                  <DialogFooter>
                    <Button type="button" variant="ghost" onClick={resetForm} disabled={isSubmitting}>
                      초기화
                    </Button>
                    <Button type="submit" disabled={isSubmitDisabled}>
                      <PlusCircle className="size-4" aria-hidden="true" />
                      {isSubmitting ? "등록 중..." : "등록"}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="mb-3 flex flex-wrap items-start justify-between gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <span>{error}</span>
              <Button size="sm" variant="outline" onClick={reload}>
                다시 시도
              </Button>
            </div>
          ) : null}
          <div className="flex flex-wrap items-center justify-between gap-2 pb-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>상태별 문의 현황</span>
              <span className="rounded-full bg-muted px-2 py-1 text-xs font-semibold text-foreground shadow-xs">
                {statusFilter ? `${statusFilter}만 보기` : "전체 보기"}
                {isMyPostsOnly ? " · 내 VOC" : ""}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant={isMyPostsOnly ? "secondary" : "outline"}
                size="sm"
                onClick={toggleMyPostsOnly}
                aria-pressed={isMyPostsOnly}
              >
                내 VOC
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={clearStatusFilter}
                disabled={!statusFilter}
              >
                필터 해제
              </Button>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <button
              type="button"
              onClick={clearStatusFilter}
              className={`rounded-lg border px-4 py-2 text-left shadow-xs transition hover:border-primary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 ${!statusFilter ? "border-primary bg-primary/10" : "bg-muted/40"
                }`}
              aria-pressed={!statusFilter}
              aria-label="모든 상태 보기"
            >
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>전체</span>
                <Badge variant="outline" className="border-primary/40 text-[11px]">
                  all
                </Badge>
              </div>
              <div className="mt-2 text-2xl font-semibold">{totalPosts}</div>
            </button>
            {STATUS_OPTIONS.map((option) => (
              <button
                type="button"
                key={option.value}
                onClick={() => toggleStatusFilter(option.value)}
                className={`rounded-lg border px-4 py-2 text-left shadow-xs transition hover:border-primary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 ${statusFilter === option.value ? "border-primary bg-primary/10" : "bg-muted/40"
                  }`}
                aria-pressed={statusFilter === option.value}
              >
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{option.value}</span>
                  <StatusBadge status={option.value} />
                </div>
                <div className="mt-2 text-2xl font-semibold">
                  {statusCounts[option.value] ?? 0}
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <section className="grid flex-1 min-h-0 grid-rows-[1fr_auto] gap-3">
        <div
          className="min-h-0 overflow-y-auto rounded-lg border bg-background"
          aria-busy={isLoading || isRefreshing}
        >
          <Table stickyHeader className="table-fixed [&_th]:text-center [&_td]:text-center">
            <TableHeader>
              <TableRow>
                <TableHead className="w-[70px]">No</TableHead>
                <TableHead className="w-[45%] min-w-[260px]">제목</TableHead>
                <TableHead className="w-[120px]">카테고리</TableHead>
                <TableHead className="w-[120px]">상태</TableHead>
                <TableHead className="w-[120px]">작성자</TableHead>
                <TableHead className="w-[150px]">작성일</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-sm text-muted-foreground">
                    <span className="inline-flex items-center justify-center gap-2">
                      <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                      <span>VOC 게시글을 불러오는 중입니다...</span>
                    </span>
                  </TableCell>
                </TableRow>
              ) : filteredPosts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-sm text-muted-foreground">
                    {statusFilter
                      ? "선택한 상태의 글이 없습니다."
                      : "아직 등록된 글이 없습니다. 첫 문의를 남겨보세요."}
                  </TableCell>
                </TableRow>
              ) : (
                visiblePosts.map((post, index) => {
                  const isSelected = post.id === selectedPost?.id
                  const displayNumber = Math.max(
                    pagination.totalRows - (pagination.pageIndex * pagination.pageSize + index),
                    1,
                  )
                  return (
                    <TableRow
                      key={post.id}
                      onClick={() => selectPost(post.id)}
                      className={`cursor-pointer ${isSelected ? "bg-muted/60" : "hover:bg-muted/40"}`}
                      data-selected={isSelected ? "true" : undefined}
                    >
                      <TableCell className="w-[90px] text-sm font-semibold text-muted-foreground">
                        {displayNumber}
                      </TableCell>
                      <TableCell className="w-[45%] min-w-[260px] font-medium">
                        {post.title}
                      </TableCell>
                      <TableCell className="w-[120px]">
                        <Badge variant="outline" className="text-[11px]">
                          {post.app || DEFAULT_APP_CATEGORY}
                        </Badge>
                      </TableCell>
                      <TableCell className="w-[120px]">
                        <StatusBadge status={post.status} />
                      </TableCell>
                      <TableCell className="w-[120px]">
                        {post.author?.name || "작성자"}
                      </TableCell>
                      <TableCell className="w-[150px] text-xs text-muted-foreground">
                        {formatTimestamp(post.createdAt)}
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>

        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span aria-live="polite">
              {isLoading
                ? "VOC 게시글을 불러오는 중입니다..."
                : `총 ${filteredPosts.length}건 중 ${visiblePosts.length}건 표시`}
            </span>
            {statusFilter ? (
              <Badge variant="secondary" className="text-[11px]">
                {statusFilter} 상태
              </Badge>
            ) : null}
            {isRefreshing ? (
              <span className="inline-flex items-center gap-1 text-primary">
                <Loader2 className="size-3 animate-spin" aria-hidden="true" />
                새로고침 중
              </span>
            ) : null}
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                onClick={firstPage}
                disabled={pagination.currentPage <= 1}
                aria-label="Go to first page"
                title="Go to first page"
              >
                <ChevronsLeft className="size-4" aria-hidden="true" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={prevPage}
                disabled={pagination.currentPage <= 1}
                aria-label="Go to previous page"
                title="Go to previous page"
              >
                <ChevronLeft className="size-4" aria-hidden="true" />
              </Button>
              <span className="px-2 text-sm font-medium" aria-live="polite">
                Page {pagination.currentPage} of {pagination.totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={nextPage}
                disabled={pagination.currentPage >= pagination.totalPages}
                aria-label="Go to next page"
                title="Go to next page"
              >
                <ChevronRight className="size-4" aria-hidden="true" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={lastPage}
                disabled={pagination.currentPage >= pagination.totalPages}
                aria-label="Go to last page"
                title="Go to last page"
              >
                <ChevronsRight className="size-4" aria-hidden="true" />
              </Button>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <span className="text-xs text-muted-foreground">Rows per page</span>
              <select
                value={pagination.pageSize}
                onChange={(event) => changePageSize(Number(event.target.value))}
                className="h-8 rounded-md border border-input bg-background px-2 text-sm text-foreground shadow-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
                aria-label="Rows per page"
                title="Rows per page"
              >
                {[5, 8, 10, 15, 20].map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </section>

      <Dialog
        open={Boolean(isDetailOpen && selectedPost)}
        onOpenChange={handleDetailOpenChange}
      >
        <DialogContent className="w-[min(1100px,calc(100%-2rem))] min-h-[50vh] sm:max-w-5xl">
          {selectedPost ? (
            <>
              <div className="flex justify-between">
                <DialogHeader className="items-start">
                  <DialogTitle className="flex items-center gap-2">
                    <MessageSquare className="size-5" aria-hidden="true" />
                    {selectedPost.title}
                  </DialogTitle>
                  <DialogDescription className="flex flex-wrap items-center gap-2">
                    {selectedPost.author?.name || "작성자"} · {formatTimestamp(selectedPost.createdAt)}
                    <StatusBadge status={selectedPost.status} />
                    <Badge variant="outline" className="text-[11px]">
                      {selectedPost.app || DEFAULT_APP_CATEGORY}
                    </Badge>
                  </DialogDescription>
                </DialogHeader>
                <div className="flex items-end">
                  <div className="flex flex-wrap items-center gap-2">
                    <label className="text-xs text-muted-foreground" htmlFor={`${selectedPost.id}-status-modal`}>
                      상태
                    </label>
                    <select
                      id={`${selectedPost.id}-status-modal`}
                      value={selectedPost.status}
                      onChange={(event) => updateStatus(selectedPost.id, event.target.value)}
                      className="h-8 rounded-md border border-input bg-background px-2 text-xs shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                      disabled={!canDeletePost(selectedPost)}
                      title={
                        !canDeletePost(selectedPost)
                          ? "작성자 또는 관리자만 상태를 바꿀 수 있습니다."
                          : undefined
                      }
                    >
                      {STATUS_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.value}
                        </option>
                      ))}
                    </select>
                    <Button
                      type="button"
                      size="sm"
                      variant={isEditing ? "secondary" : "outline"}
                      onClick={isEditing ? handleSaveEdit : () => setIsEditing(true)}
                      disabled={!canEditSelected || isUpdating}
                      title={
                        !canEditSelected
                          ? "작성자 또는 관리자만 수정할 수 있습니다."
                          : isEditing
                            ? "수정 내용을 저장합니다."
                            : "제목과 내용을 수정합니다."
                      }
                    >
                      <Pencil className="mr-1 size-4" aria-hidden="true" />
                      {isEditing ? (isUpdating ? "저장 중..." : "저장") : "수정"}
                    </Button>
                    {isEditing ? (
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={handleCancelEdit}
                        disabled={isUpdating}
                      >
                        취소
                      </Button>
                    ) : null}
                    <Button
                      type="button"
                      size="icon-sm"
                      variant="destructive"
                      onClick={() => handleRequestDelete(selectedPost)}
                      disabled={!canDeletePost(selectedPost)}
                      title={
                        !canDeletePost(selectedPost)
                          ? "작성자 또는 관리자만 삭제할 수 있습니다."
                          : "글을 삭제합니다."
                      }
                    >
                      <Trash2 className="size-4" aria-hidden="true" />
                    </Button>
                  </div>
                </div>
              </div>

              {isEditing ? (
                <div className="space-y-3">
                  <Input
                    value={editForm.title}
                    onChange={(event) =>
                      setEditForm((prev) => ({ ...prev, title: event.target.value }))
                    }
                    placeholder="제목을 입력하세요"
                    disabled={isUpdating}
                  />
                  <RichTextEditor
                    id="voc-edit-editor"
                    value={editForm.content}
                    onChange={(value) => setEditForm((prev) => ({ ...prev, content: value }))}
                    modules={QUILL_MODULES}
                    formats={QUILL_FORMATS}
                    ariaLabel="게시글 내용 수정"
                    readOnly={isUpdating}
                  />
                </div>
              ) : (
                <PostContent
                  content={selectedPost.content}
                  className="min-h-[160px] max-h-[60vh]"
                  allowResize
                />
              )}
              <div className="space-y-7 rounded-md bg-muted/30 px-3 py-1">
                {selectedPost.replies.length === 0 ? (
                  <p className="text-xs text-muted-foreground">아직 답변이 없습니다.</p>
                ) : (
                  selectedPost.replies.map((reply) => (
                    <div key={reply.id} className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline">답변</Badge>
                        <span className="font-medium text-foreground">{reply.author?.name || "응답자"}</span>
                        <span aria-hidden="true">·</span>
                        <span>{formatTimestamp(reply.createdAt)}</span>
                      </div>
                      <p className="text-sm text-foreground/90">{reply.content}</p>
                    </div>
                  ))
                )}
              </div>

              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <Input
                  value={replyDraftValue}
                  onChange={(event) => updateReplyDraft(selectedPost.id, event.target.value)}
                  placeholder="답변을 남겨주세요"
                  disabled={isReplying}
                />
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => addReply(selectedPost.id)}
                  disabled={isReplyDisabled}
                >
                  {isReplying ? (
                    <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                  ) : (
                    <Reply className="size-4" aria-hidden="true" />
                  )}
                  {isReplying ? "등록 중..." : "답변 등록"}
                </Button>
              </div>
            </>
          ) : null}
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(deleteTarget)} onOpenChange={handleDeleteDialogOpenChange}>
        <DialogContent className="sm:max-w-sm" aria-describedby="voc-delete-description">
          <DialogHeader>
            <DialogTitle>게시글 삭제</DialogTitle>
            <DialogDescription id="voc-delete-description">
              {`"${deleteTarget?.title || "선택한 게시글"}"을(를) 삭제할까요?`}
              <br />
              답변을 포함해 게시글의 모든 내용이 사라집니다.
            </DialogDescription>
          </DialogHeader>
          <div className="rounded-md bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
            {deleteTarget?.title || deleteTarget?.id || "선택한 게시글"}
          </div>
          <DialogFooter className="sm:justify-end">
            <Button type="button" variant="ghost" onClick={() => setDeleteTarget(null)}>
              취소
            </Button>
            <Button type="button" variant="destructive" onClick={handleConfirmDelete}>
              삭제
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
