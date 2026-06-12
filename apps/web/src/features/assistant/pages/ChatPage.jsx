import { useEffect, useRef, useState } from "react"
import { useLocation, useOutletContext } from "react-router-dom"
import { Bot, PanelLeft, Plus, RefreshCw, Settings } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ChatComposer } from "../components/ChatComposer"
import { ChatErrorBanner } from "../components/ChatErrorBanner"
import { ChatMessages } from "../components/ChatMessages"
import { RoomList } from "../components/RoomList"
import { RagIndexMultiSelect } from "../components/RagIndexMultiSelect"
import { useAssistantRagIndex } from "../hooks/useAssistantRagIndex"
import { useChatSession } from "../hooks/useChatSession"
import { sortRoomsByRecentQuestion } from "../utils/chatRooms"

export function ChatPage() {
  const location = useLocation()
  const outletContext = useOutletContext() || {}
  const availableMailboxes = Array.isArray(outletContext.availableMailboxes)
    ? outletContext.availableMailboxes
    : []
  const ragSettings = useAssistantRagIndex()
  const handoffMessages = Array.isArray(location?.state?.initialMessages)
    ? location.state.initialMessages
    : undefined
  const initialRooms = Array.isArray(location?.state?.initialRooms)
    ? location.state.initialRooms
    : undefined
  const initialMessagesByRoom =
    location?.state?.initialMessagesByRoom && typeof location.state.initialMessagesByRoom === "object"
      ? location.state.initialMessagesByRoom
      : undefined
  const initialActiveRoomId =
    typeof location?.state?.initialActiveRoomId === "string"
      ? location.state.initialActiveRoomId
      : undefined

  const {
    rooms,
    activeRoomId,
    messages,
    messagesByRoom,
    isSending,
    errorMessage,
    clearError,
    sendMessage,
    resetConversation,
    selectRoom,
    createRoom,
    removeRoom,
  } = useChatSession({
    initialMessages: handoffMessages,
    initialRooms,
    initialMessagesByRoom,
    initialActiveRoomId,
    permissionGroups: ragSettings.permissionGroups,
    ragIndexNames: ragSettings.ragIndexNames,
  })

  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [input, setInput] = useState("")
  const inputRef = useRef(null)
  const wasSendingRef = useRef(false)
  const activeRoom = rooms.find((room) => room.id === activeRoomId) || rooms[0] || { name: "대화방" }

  const sortedRooms = sortRoomsByRecentQuestion(rooms, messagesByRoom)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    if (!isSending && wasSendingRef.current && inputRef.current) {
      inputRef.current.focus()
    }
    wasSendingRef.current = isSending
  }, [isSending])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!input.trim() || isSending) return
    try {
      await sendMessage(input)
      setInput("")
    } finally {
      inputRef.current?.focus()
    }
  }

  const handleDeleteRoom = (roomId) => {
    removeRoom(roomId)
  }

  const handleSelectRoom = (roomId) => {
    setIsSettingsOpen(false)
    selectRoom(roomId)
  }

  const handleCreateRoom = () => {
    setIsSettingsOpen(false)
    createRoom()
  }

  const handleResetConversation = () => {
    setIsSettingsOpen(false)
    resetConversation(activeRoomId)
  }

  const handleToggleSettings = () => {
    setIsSettingsOpen((prev) => !prev)
  }

  return (
    <div className="grid h-full min-h-0 grid-rows-[auto_1fr] gap-4 overflow-hidden">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight">Etch AI Assistant</p>
            <p className="text-xs text-muted-foreground">Etch기술팀 AI Chatbot 입니다.</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="flex h-2 w-2 rounded-full bg-primary ring-2 ring-primary/30" />
          <span>현재 대화방: {activeRoom.name}</span>
        </div>
      </header>

      <div className="grid min-h-0 grid-rows-[auto_1fr] gap-3 rounded-xl border bg-card shadow-sm">
        <div className="flex flex-col gap-2 border-b bg-card px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant={isSidebarOpen ? "secondary" : "outline"}
                size="icon"
                className="h-9 w-9"
                onClick={() => setIsSidebarOpen((prev) => !prev)}
                aria-label={isSidebarOpen ? "대화방 목록 닫기" : "대화방 목록 열기"}
              >
                <PanelLeft className="h-4 w-4" />
              </Button>
              <div className="flex items-center gap-3">
                <span className="flex h-2 w-2 rounded-full bg-primary ring-2 ring-primary/30" />
                <p className="text-sm font-semibold leading-tight">Etch AI Assistant</p>
                <span className="text-xs text-muted-foreground">실시간 상담</span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9"
                onClick={handleCreateRoom}
                aria-label="새 대화방 만들기"
              >
                <Plus className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9"
                onClick={handleResetConversation}
                disabled={isSending}
                aria-label="현재 대화 초기화"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
            <div className="flex flex-wrap items-center gap-1">
              <span>RAG 인덱스</span>
              {ragSettings.ragIndexNames.map((value) => (
                <Badge key={value} variant="secondary" className="text-[11px]">
                  {value}
                </Badge>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-1">
              <span>권한 그룹</span>
              {ragSettings.permissionGroups.map((value) => (
                <Badge key={value} variant="secondary" className="text-[11px]">
                  {value}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        <div className="grid min-h-0 grid-cols-1 overflow-hidden lg:grid-cols-[280px_1fr]">
          {isSidebarOpen ? (
            <aside className="flex min-h-0 flex-col border-r bg-muted/40">
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
              <div className="mb-2 flex items-center justify-between border-b px-3 pb-2">
                <span className="text-[11px] text-muted-foreground">방을 선택하세요</span>
              </div>
              <div className="flex-1 min-h-0 overflow-y-auto px-2 pb-3">
                <RoomList
                  rooms={sortedRooms}
                  activeRoomId={activeRoomId}
                  onSelectRoom={handleSelectRoom}
                  onDeleteRoom={handleDeleteRoom}
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

          <div className="flex min-h-0 flex-col">
            {isSettingsOpen ? (
              <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
                <div className="flex items-center gap-2 border-b px-4 py-3">
                  <Settings className="h-4 w-4 text-muted-foreground" />
                  <p className="text-sm font-semibold">RAG 설정</p>
                </div>
                <div className="flex-1 min-h-0 overflow-y-auto px-4 py-3">
                  <div className="grid gap-3">
                    <RagIndexMultiSelect
                      label="RAG 인덱스"
                      values={ragSettings.ragIndexNames}
                      onChange={ragSettings.setRagIndexNames}
                      placeholder="rp-unclassified"
                      helperText="목록에서 선택 · 최소 1개 필수"
                      options={ragSettings.ragIndexOptions}
                      isDisabled={ragSettings.isLoading}
                    />
                    <RagIndexMultiSelect
                      label="권한 그룹"
                      values={ragSettings.permissionGroups}
                      onChange={ragSettings.setPermissionGroups}
                      placeholder="rag-public"
                      helperText="목록에서 선택 · 최소 1개 필수"
                      options={ragSettings.permissionGroupOptions}
                      isDisabled={ragSettings.isLoading}
                    />
                    {ragSettings.isError ? (
                      <p className="text-[11px] text-destructive">
                        {ragSettings.errorMessage || "RAG 설정을 불러오지 못했어요."}
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
                  availableMailboxes={availableMailboxes}
                />

                <ChatErrorBanner message={errorMessage} onDismiss={clearError} />

                <ChatComposer
                  inputId="assistant-page-input"
                  label="어시스턴트에게 질문하기"
                  inputRef={inputRef}
                  inputValue={input}
                  onInputChange={(event) => setInput(event.target.value)}
                  onSubmit={handleSubmit}
                  isSending={isSending}
                  placeholder="궁금한 점을 입력하세요. Shift+Enter로 줄바꿈"
                  footerLeft="베타 · LLM API 연결"
                  footerRight="Shift+Enter로 줄바꿈"
                />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
