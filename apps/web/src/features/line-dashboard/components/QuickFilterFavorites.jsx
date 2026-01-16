// src/features/line-dashboard/components/QuickFilterFavorites.jsx
import * as React from "react"
import { IconChevronDown } from "@tabler/icons-react"
import { BookmarkCheck, BookmarkPlus, BookmarkX } from "lucide-react"
import { toast } from "sonner"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { QuickFilterFieldset } from "./QuickFilterSections"
import { buildToastOptions } from "../utils/toast"

function buildDefaultFavoriteName() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")
  const hours = String(now.getHours()).padStart(2, "0")
  const minutes = String(now.getMinutes()).padStart(2, "0")
  return `Bookmark_${month}/${day}_${hours}:${minutes}`
}

function normalizeForCompare(value) {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeForCompare(item))
  }
  if (value && typeof value === "object") {
    const sortedKeys = Object.keys(value).sort()
    const normalized = {}
    sortedKeys.forEach((key) => {
      normalized[key] = normalizeForCompare(value[key])
    })
    return normalized
  }
  return value
}

function areFiltersEqual(left, right) {
  return JSON.stringify(normalizeForCompare(left)) === JSON.stringify(normalizeForCompare(right))
}

export function QuickFilterFavorites({
  filters,
  favorites = [],
  onSaveFavorite,
  onUpdateFavorite,
  onApplyFavorite,
  onDeleteFavorite,
  resetSignal,
  className,
}) {
  const [selectedFavoriteId, setSelectedFavoriteId] = React.useState("")
  const hasMountedRef = React.useRef(false)
  const selectedFavorite =
    selectedFavoriteId && Array.isArray(favorites)
      ? favorites.find((favorite) => favorite.id === selectedFavoriteId)
      : undefined
  const hasFavoriteChanges =
    Boolean(selectedFavorite) && !areFiltersEqual(filters, selectedFavorite.filters)

  React.useEffect(() => {
    if (!Array.isArray(favorites) || favorites.length === 0) {
      setSelectedFavoriteId("")
      return
    }

    if (!selectedFavoriteId) return

    const exists = favorites.some((favorite) => favorite.id === selectedFavoriteId)
    if (!exists) {
      setSelectedFavoriteId(favorites[0].id)
    }
  }, [favorites, selectedFavoriteId])

  React.useEffect(() => {
    if (!resetSignal) {
      hasMountedRef.current = true
      return
    }
    if (!hasMountedRef.current) {
      hasMountedRef.current = true
      return
    }
    setSelectedFavoriteId("")
  }, [resetSignal])

  const handleSelectFavorite = (favoriteId) => {
    setSelectedFavoriteId(favoriteId)
    if (!favoriteId || typeof onApplyFavorite !== "function") return
    onApplyFavorite(favoriteId)
  }

  const handleUpdateFavorite = () => {
    if (!selectedFavorite || !hasFavoriteChanges || typeof onUpdateFavorite !== "function")
      return
    const nextId = onUpdateFavorite(selectedFavorite.id, selectedFavorite.name)
    if (nextId) {
      setSelectedFavoriteId(nextId)
      toast.success("즐겨찾기를 업데이트했어요", {
        description: "현재 필터설정이 즐겨찾기에 저장되었습니다.",
        icon: <BookmarkCheck className="h-5 w-5 text-[var(--normal-text)]" />,
        ...buildToastOptions({ intent: "success", duration: 1800 }),
      })
    }
  }

  const handleAddFavorite = (name) => {
    if (typeof onSaveFavorite !== "function") return
    const finalName = (name ?? "").trim() || buildDefaultFavoriteName()

    const normalizedName = finalName.toLowerCase()
    const isDuplicateName =
      Array.isArray(favorites) &&
      favorites.some((favorite) => {
        const favoriteName = typeof favorite?.name === "string" ? favorite.name.trim() : ""
        return favoriteName.toLowerCase() === normalizedName
      })

    if (isDuplicateName) {
      toast.warning("중복된 즐겨찾기 이름이에요", {
        description: "다른 이름으로 저장해주세요.",
        icon: <BookmarkX className="h-5 w-5 text-[var(--normal-text)]" />,
        ...buildToastOptions({ intent: "warning", duration: 2000 }),
      })
      return
    }

    const id = onSaveFavorite(finalName)
    if (id) {
      setSelectedFavoriteId(id)
      toast.success("즐겨찾기를 추가했어요", {
        description: "현재 필터설정이 새 즐겨찾기에 저장되었습니다.",
        icon: <BookmarkPlus className="h-5 w-5 text-[var(--normal-text)]" />,
        ...buildToastOptions({ intent: "success", duration: 1800 }),
      })
    }
  }

  const handleDeleteFavorite = (favoriteId) => {
    onDeleteFavorite?.(favoriteId)
    if (favoriteId === selectedFavoriteId) {
      setSelectedFavoriteId("")
    }
  }

  const hasFavoriteActions =
    typeof onSaveFavorite === "function" ||
    typeof onApplyFavorite === "function" ||
    typeof onDeleteFavorite === "function"

  if (!hasFavoriteActions || !Array.isArray(favorites)) return null

  return (
    <FavoriteFiltersSection
      className={cn("min-w-[16rem]", className)}
      favorites={favorites}
      selectedId={selectedFavoriteId}
      onSelectFavorite={handleSelectFavorite}
      onUpdateFavorite={handleUpdateFavorite}
      showUpdateButton={hasFavoriteChanges}
      onDeleteFavorite={handleDeleteFavorite}
      onAddFavorite={handleAddFavorite}
      defaultFavoriteName={buildDefaultFavoriteName()}
    />
  )
}

function FavoriteFiltersSection({
  favorites,
  selectedId,
  onSelectFavorite,
  onUpdateFavorite,
  onDeleteFavorite,
  onAddFavorite,
  showUpdateButton,
  className,
  defaultFavoriteName = buildDefaultFavoriteName(),
}) {
  const canUpdate = showUpdateButton && typeof onUpdateFavorite === "function"
  const [newFavoriteName, setNewFavoriteName] = React.useState("")
  const [deleteTarget, setDeleteTarget] = React.useState(null)
  const isDeleteDialogOpen = Boolean(deleteTarget)
  const deleteTargetName = deleteTarget?.name ?? ""
  const deleteTargetLabel = deleteTargetName || "선택한 즐겨찾기"

  const handleSelect = (favoriteId) => {
    onSelectFavorite?.(favoriteId)
  }

  const handleCreateFavorite = () => {
    const createdId = onAddFavorite?.(newFavoriteName.trim() || defaultFavoriteName)
    if (createdId) {
      setNewFavoriteName("")
    }
  }

  const handleRequestDelete = (favorite) => {
    if (typeof onDeleteFavorite !== "function") return
    setDeleteTarget(favorite)
  }

  const handleConfirmDelete = () => {
    if (deleteTarget?.id && typeof onDeleteFavorite === "function") {
      onDeleteFavorite(deleteTarget.id)
    }
    setDeleteTarget(null)
  }

  return (
    <QuickFilterFieldset
      legendId="legend-favorites"
      label="즐겨찾기"
      className={className}
      isLegendHidden
    >
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-end gap-2">
          {canUpdate ? (
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={onUpdateFavorite}
              className="border-primary/60 text-primary hover:bg-primary/10"
            >
              업데이트
            </Button>
          ) : null}
          <div className="flex flex-col items-start gap-1">
            <span className="text-[10px] pl-2 font-semibold uppercase tracking-wide text-muted-foreground">
              즐겨찾기
            </span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className="flex h-8 w-64 items-center justify-between rounded-md border border-input bg-background px-3 text-xs font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <span
                    className={cn(
                      "truncate text-left",
                      !selectedId && "text-muted-foreground"
                    )}
                  >
                    {selectedId
                      ? favorites.find((favorite) => favorite.id === selectedId)?.name ?? ""
                      : "없음"}
                  </span>
                  <IconChevronDown className="size-4 shrink-0" aria-hidden />
                </button>
              </DropdownMenuTrigger>

              <DropdownMenuContent align="start" className="w-64 p-1">
                <DropdownMenuItem
                  className="text-xs text-muted-foreground"
                  onSelect={(event) => {
                    event.preventDefault()
                    handleSelect("")
                  }}
                >
                  없음
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {favorites.map((favorite) => (
                  <DropdownMenuItem
                    key={favorite.id}
                    className="flex items-center justify-between gap-2 text-xs"
                    onSelect={(event) => {
                      event.preventDefault()
                      handleSelect(favorite.id)
                    }}
                  >
                    <span className="truncate">{favorite.name}</span>
                    <button
                      type="button"
                      onClick={(event) => {
                        event.preventDefault()
                        event.stopPropagation()
                        handleRequestDelete(favorite)
                      }}
                      className="text-[11px] font-medium text-destructive hover:underline"
                    >
                      삭제
                    </button>
                  </DropdownMenuItem>
                ))}
                <DropdownMenuSeparator />
                <div className="flex flex-col gap-2 p-2">
                  <div className="text-[11px] font-semibold text-muted-foreground">
                    즐겨찾기 추가
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={newFavoriteName}
                      onChange={(event) => setNewFavoriteName(event.target.value)}
                      placeholder={defaultFavoriteName}
                      onKeyDown={(event) => event.stopPropagation()}
                      className="flex-1 rounded-md border border-input bg-background px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
                    />
                    <button
                      type="button"
                      onClick={(event) => {
                        event.preventDefault()
                        event.stopPropagation()
                        handleCreateFavorite()
                      }}
                      className="h-8 flex-shrink-0 rounded-md border border-input bg-background px-3 text-xs font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      추가
                    </button>
                  </div>
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      <Dialog
        open={isDeleteDialogOpen}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) setDeleteTarget(null)
        }}
      >
        <DialogContent
          className="sm:max-w-sm"
          aria-describedby="favorite-delete-description"
        >
          <DialogHeader>
            <DialogTitle>즐겨찾기 삭제</DialogTitle>
            <DialogDescription id="favorite-delete-description">
              {`"${deleteTargetLabel}"을(를) 삭제할까요?`}
              <br />
              저장된 퀵 필터 구성이 사라집니다.
            </DialogDescription>
          </DialogHeader>
          <div className="rounded-md bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
            {deleteTargetLabel}
          </div>
          <DialogFooter className="sm:justify-end">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setDeleteTarget(null)}
            >
              취소
            </Button>
            <Button type="button" variant="destructive" onClick={handleConfirmDelete}>
              삭제
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </QuickFilterFieldset>
  )
}
