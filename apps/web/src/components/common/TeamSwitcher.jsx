// 파일 경로: src/components/common/TeamSwitcher.jsx
import * as React from "react"
import { ChevronsUpDown, Plus } from "lucide-react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import {
  isSameTeamOption,
  normalizeTeamId,
  normalizeTeamOption,
  readStoredTeamOption,
  writeStoredTeamOption,
} from "@/lib/affiliation"

/* -----------------------------------------------------------------------------
 * 유틸: 표기 처리
 * ---------------------------------------------------------------------------*/

const UNKNOWN_OPTION = {
  id: "unknown",
  label: "Unknown",
  description: "",
  lineId: null,
  userSdwtProd: "",
}

/** 라벨에서 머리글자(이니셜) 추출: 'LINE-01' -> 'L1' 등 */
function getInitials(label) {
  if (!label) return "?"
  const parts = label.split(/[\s-_]+/).filter(Boolean)
  if (parts.length === 0) return label.slice(0, 2).toUpperCase()
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
}

/* -----------------------------------------------------------------------------
 * 컴포넌트
 * ---------------------------------------------------------------------------*/

/**
 * 팀 스위처
 * - 사이드바 상단에서 선택 값을 표시/변경하는 드롭다운
 * - 옵션이 없어도 저장값/알 수 없음으로 표시
 */
export function TeamSwitcher({
  options: optionsProp,
  activeId,
  onSelect,
  menuLabel = "Production Lines",
  manageLabel = "Manage lines",
  ariaLabel,
  disabled = false,
}) {
  const { isMobile } = useSidebar()

  const source = Array.isArray(optionsProp) ? optionsProp : []
  const options = source.map(normalizeTeamOption).filter(Boolean)
  const storedOption = readStoredTeamOption()
  const fallbackOption = options[0] ?? storedOption ?? UNKNOWN_OPTION

  const resolvedActiveId = normalizeTeamId(activeId) ?? fallbackOption.id
  const matchedStoredOption =
    storedOption && storedOption.id === resolvedActiveId ? storedOption : null
  const activeOption =
    options.find((option) => option.id === resolvedActiveId) ??
    matchedStoredOption ??
    fallbackOption
  const activeAvatarLabel = activeOption.lineId || activeOption.label
  const hasOptions = options.length > 0

  React.useEffect(() => {
    if (!activeOption || activeOption.id === UNKNOWN_OPTION.id) return
    if (isSameTeamOption(activeOption, storedOption)) return
    writeStoredTeamOption(activeOption)
  }, [activeOption, storedOption])

  const handleSelect = (nextId) => {
    if (disabled) return
    const normalizedNextId = normalizeTeamId(nextId)
    if (!normalizedNextId || normalizedNextId === resolvedActiveId) return
    if (normalizedNextId === UNKNOWN_OPTION.id) return

    const nextOption = options.find((option) => option.id === normalizedNextId)
    onSelect?.(normalizedNextId, nextOption)
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild disabled={disabled}>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
              aria-label={ariaLabel}
              disabled={disabled}
              aria-disabled={disabled || undefined}
            >
              <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg font-semibold">
                {getInitials(activeAvatarLabel)}
              </div>

              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">{activeOption.label}</span>
                {activeOption.description ? (
                  <span className="truncate text-xs text-muted-foreground">
                    {activeOption.description}
                  </span>
                ) : null}
              </div>

              <ChevronsUpDown className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>

          <DropdownMenuContent
            className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
            align="start"
            side={isMobile ? "bottom" : "right"}
            sideOffset={4}
          >
            <DropdownMenuLabel className="text-muted-foreground text-xs">
              {menuLabel}
            </DropdownMenuLabel>

            {hasOptions
              ? options.map((line) => {
                const isActive = line.id === resolvedActiveId
                const avatarLabel = line.lineId || line.label
                return (
                  <DropdownMenuItem
                    key={line.id}
                    className={cn(
                      "gap-2 p-2",
                      isActive && "bg-sidebar-accent/20 focus:bg-sidebar-accent/20",
                    )}
                    onSelect={() => handleSelect(line.id)}
                  >
                    <div className="flex size-6 items-center justify-center rounded-md border text-xs font-semibold">
                      {getInitials(avatarLabel)}
                    </div>

                    <div className="flex flex-col">
                      <span>{line.label}</span>
                      {line.description ? (
                        <span className="text-muted-foreground text-xs">{line.description}</span>
                      ) : null}
                    </div>
                  </DropdownMenuItem>
                )
              })
              : (
                <DropdownMenuItem
                  key="__unknown__"
                  className="gap-2 p-2 opacity-70"
                  disabled
                >
                  <div className="flex size-6 items-center justify-center rounded-md border text-xs font-semibold">
                    {getInitials("Unknown")}
                  </div>
                  <div className="flex flex-col">
                    <span>Unknown</span>
                    <span className="text-muted-foreground text-xs">
                      사용할 라인 옵션이 없습니다.
                    </span>
                  </div>
                </DropdownMenuItem>
              )
            }

            <DropdownMenuSeparator />
            <DropdownMenuItem className="gap-2 p-2" disabled>
              <div className="flex size-6 items-center justify-center rounded-md border bg-transparent">
                <Plus className="size-4" />
              </div>
              <div className="text-muted-foreground font-medium">{manageLabel}</div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
