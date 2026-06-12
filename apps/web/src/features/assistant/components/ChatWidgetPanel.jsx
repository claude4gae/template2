import { useState } from "react"
import { Maximize, Minimize2, Minus, PanelLeft, Settings } from "lucide-react"

import { Button } from "@/components/ui/button"

import { ChatComposer } from "./ChatComposer"
import { ChatErrorBanner } from "./ChatErrorBanner"
import { ChatMessages } from "./ChatMessages"
import { RoomList } from "./RoomList"
import { RagIndexMultiSelect } from "./RagIndexMultiSelect"

export function ChatWidgetPanel({
  containerRef,
  widgetPosition,
  size,
  isMaximized,
  onResizePointerDown,
  onHeaderPointerDown,
  isSidebarOpen,
  onToggleSidebar,
  ragSettings,
  rooms,
  sortedRooms,
  activeRoomId,
  onSelectRoom,
  onDeleteRoom,
  onCreateRoom,
  messages,
  isSending,
  availableMailboxes = [],
  errorMessage,
  onClearError,
  inputRef,
  inputValue,
  onInputChange,
  onSubmit,
  onOpenFullChat,
  onRestoreDefaultSize,
  onClose,
}) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const {
    permissionGroups,
    setPermissionGroups,
    ragIndexNames,
    setRagIndexNames,
    permissionGroupOptions,
    ragIndexOptions,
    isLoading: isRagSettingsLoading,
    isError: isRagSettingsError,
    errorMessage: ragSettingsErrorMessage,
  } = ragSettings

  const handleSelectRoom = (roomId) => {
    setIsSettingsOpen(false)
    onSelectRoom(roomId)
  }

  const handleCreateRoom = () => {
    setIsSettingsOpen(false)
    onCreateRoom()
  }

  const handleToggleSettings = () => {
    setIsSettingsOpen((prev) => !prev)
  }

  return (
    <div
      ref={containerRef}
      className="fixed z-50"
      style={{
        left: widgetPosition.x,
        top: widgetPosition.y,
        width: size.width,
        maxWidth: isMaximized ? "100vw" : "calc(100vw - 16px)",
      }}
    >
      <div
        className={`relative flex flex-col overflow-hidden rounded-xl border bg-card shadow-2xl ${
          isMaximized ? "max-h-none" : "max-h-[80vh]"
        }`}
        style={{ height: size.height }}
      >
        <div className="pointer-events-none absolute inset-0">
          <div
            className="absolute inset-y-0 left-0 w-2 cursor-ew-resize pointer-events-auto"
            onPointerDown={onResizePointerDown("w")}
            role="presentation"
          />
          <div
            className="absolute inset-y-0 right-0 w-2 cursor-ew-resize pointer-events-auto"
            onPointerDown={onResizePointerDown("e")}
            role="presentation"
          />
          <div
            className="absolute inset-x-0 top-0 h-2 cursor-ns-resize pointer-events-auto"
            onPointerDown={onResizePointerDown("n")}
            role="presentation"
          />
          <div
            className="absolute inset-x-0 bottom-0 h-2 cursor-ns-resize pointer-events-auto"
            onPointerDown={onResizePointerDown("s")}
            role="presentation"
          />
          <div
            className="absolute left-0 top-0 h-3 w-3 cursor-nwse-resize pointer-events-auto"
            onPointerDown={onResizePointerDown("nw")}
            role="presentation"
          />
          <div
            className="absolute right-0 top-0 h-3 w-3 cursor-nesw-resize pointer-events-auto"
            onPointerDown={onResizePointerDown("ne")}
            role="presentation"
          />
          <div
            className="absolute bottom-0 left-0 h-3 w-3 cursor-nesw-resize pointer-events-auto"
            onPointerDown={onResizePointerDown("sw")}
            role="presentation"
          />
          <div
            className="absolute bottom-0 right-0 h-3 w-3 cursor-nwse-resize pointer-events-auto"
            onPointerDown={onResizePointerDown("se")}
            role="presentation"
          />
        </div>

        <div
          className="flex shrink-0 touch-none flex-col gap-2 border-b bg-card px-4 py-3 cursor-grab active:cursor-grabbing"
          onPointerDown={onHeaderPointerDown}
          role="presentation"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={onToggleSidebar}
                aria-label={isSidebarOpen ? "대화방 목록 닫기" : "대화방 목록 열기"}
              >
                <PanelLeft className="h-3 w-3" />
              </Button>

              <div className="mx-3 flex items-center gap-3">
                <span className="flex h-2 w-2 rounded-full bg-primary ring-2 ring-primary/30" />
                <p className="text-sm font-semibold leading-tight">Etch AI Assistant</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={onOpenFullChat}
                aria-label="Open full chat page"
              >
                <Maximize className="h-4 w-4" />
              </Button>

              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={onRestoreDefaultSize}
                aria-label="작게 보기"
              >
                <Minimize2 className="h-4 w-4" />
              </Button>

              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={onClose}
                aria-label="Minimize chat widget"
              >
                <Minus className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="grid gap-2" data-chat-widget-no-drag="true">
            <div className="grid gap-2 sm:grid-cols-2">
              <RagIndexMultiSelect
                label="RAG 인덱스"
                values={ragIndexNames}
                onChange={setRagIndexNames}
                placeholder="rp-unclassified"
                options={ragIndexOptions}
                isDisabled={isRagSettingsLoading}
                showSelectionBadges={false}
              />
              <RagIndexMultiSelect
                label="권한 그룹"
                values={permissionGroups}
                onChange={setPermissionGroups}
                placeholder="rag-public"
                options={permissionGroupOptions}
                isDisabled={isRagSettingsLoading}
                showSelectionBadges={false}
              />
            </div>
            {isRagSettingsError ? (
              <p className="text-[11px] text-destructive">
                {ragSettingsErrorMessage || "RAG 설정을 불러오지 못했어요."}
              </p>
            ) : null}
          </div>
        </div>

        <div className="flex flex-1 min-h-0 overflow-hidden">
          {isSidebarOpen ? (
            <aside className="flex w-52 shrink-0 min-h-0 flex-col border-r bg-muted/40">
              <div className="flex items-center justify-between px-3 py-2">
                <div className="space-y-0.5">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">대화방</p>
                  <p className="text-sm font-semibold text-foreground">최근 {rooms.length}개</p>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  className="h-8 px-3 text-xs"
                  onClick={handleCreateRoom}
                >
                  새 대화
                </Button>
              </div>
              <div className="mb-2 flex items-center justify-between border-b px-3 pb-2" />
              <div className="flex-1 min-h-0 overflow-y-auto px-2 pb-3">
                <RoomList
                  rooms={sortedRooms}
                  activeRoomId={activeRoomId}
                  onSelectRoom={handleSelectRoom}
                  onDeleteRoom={onDeleteRoom}
                />
              </div>
              <div className="border-t px-3 py-3">
                <Button
                  variant={isSettingsOpen ? "secondary" : "outline"}
                  size="sm"
                  className="h-9 w-full justify-between"
                  onClick={handleToggleSettings}
                >
                  <span className="text-xs font-semibold">설정</span>
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </aside>
          ) : null}

          <div className="flex flex-1 min-h-0 flex-col overflow-hidden">
            {isSettingsOpen ? (
              <div className="flex flex-1 min-h-0 flex-col overflow-hidden">
                <div className="flex items-center gap-2 border-b px-4 py-3">
                  <Settings className="h-4 w-4 text-muted-foreground" />
                  <p className="text-sm font-semibold">RAG 설정</p>
                </div>
                <div className="flex-1 min-h-0 overflow-y-auto px-4 py-3">
                  <div className="grid gap-3">
                    <RagIndexMultiSelect
                      label="RAG 인덱스"
                      values={ragIndexNames}
                      onChange={setRagIndexNames}
                      placeholder="rp-unclassified"
                      helperText="목록에서 선택 · 최소 1개 필수"
                      options={ragIndexOptions}
                      isDisabled={isRagSettingsLoading}
                    />
                    <RagIndexMultiSelect
                      label="권한 그룹"
                      values={permissionGroups}
                      onChange={setPermissionGroups}
                      placeholder="rag-public"
                      helperText="목록에서 선택 · 최소 1개 필수"
                      options={permissionGroupOptions}
                      isDisabled={isRagSettingsLoading}
                    />
                    {isRagSettingsError ? (
                      <p className="text-[11px] text-destructive">
                        {ragSettingsErrorMessage || "RAG 설정을 불러오지 못했어요."}
                      </p>
                    ) : null}
                  </div>
                </div>
              </div>
            ) : (
              <>
                <ChatMessages
                  messages={messages}
                  isSending={isSending}
                  fillBubbles
                  availableMailboxes={availableMailboxes}
                />

                <ChatErrorBanner message={errorMessage} onDismiss={onClearError} />

                <ChatComposer
                  inputId="chat-widget-input"
                  label="어시스턴트에게 질문하기"
                  inputRef={inputRef}
                  inputValue={inputValue}
                  onInputChange={onInputChange}
                  onSubmit={onSubmit}
                  isSending={isSending}
                  placeholder="궁금한 점을 입력하세요. Shift+Enter로 줄바꿈"
                  footerLeft={
                    <button
                      type="button"
                      className="text-primary underline underline-offset-4"
                      onClick={onOpenFullChat}
                    >
                      전체 화면에서 이어서 보기
                    </button>
                  }
                  footerRight="베타 · LLM API 연결"
                />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
