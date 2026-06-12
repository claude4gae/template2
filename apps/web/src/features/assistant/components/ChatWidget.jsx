import { useEffect, useRef, useState } from "react"
import { useLocation } from "react-router-dom"

import { ChatWidgetLauncher } from "./ChatWidgetLauncher"
import { ChatWidgetPanel } from "./ChatWidgetPanel"
import { useAttentionTooltip } from "../hooks/useAttentionTooltip"
import { useAssistantRagIndex } from "../hooks/useAssistantRagIndex"
import { useChatSession } from "../hooks/useChatSession"
import { sortRoomsByRecentQuestion } from "../utils/chatRooms"
import {
  DEFAULT_CHAT_HEIGHT,
  DEFAULT_CHAT_WIDTH,
  DEFAULT_FLOATING_BUTTON_SIZE,
  clampPosition,
  clampSize,
} from "../utils/chatWidgetBounds"

export function ChatWidget({ availableMailboxes = [] }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isMaximized, setIsMaximized] = useState(false)
  const [input, setInput] = useState("")
  const [buttonPosition, setButtonPosition] = useState({ x: null, y: null })
  const [isDragging, setIsDragging] = useState(false)
  const [widgetPosition, setWidgetPosition] = useState({ x: null, y: null })
  const [isWidgetDragging, setIsWidgetDragging] = useState(false)
  const [isResizing, setIsResizing] = useState(false)
  const [size, setSize] = useState(() => clampSize(DEFAULT_CHAT_WIDTH, DEFAULT_CHAT_HEIGHT))
  const location = useLocation()
  const sizeRef = useRef(size)
  const ragSettings = useAssistantRagIndex()
  const {
    rooms,
    activeRoomId,
    messages,
    messagesByRoom,
    isSending,
    errorMessage,
    clearError,
    sendMessage,
    selectRoom,
    createRoom,
    removeRoom,
  } = useChatSession({
    permissionGroups: ragSettings.permissionGroups,
    ragIndexNames: ragSettings.ragIndexNames,
  })
  const inputRef = useRef(null)
  const floatingButtonRef = useRef(null)
  const floatingButtonSizeRef = useRef({
    width: DEFAULT_FLOATING_BUTTON_SIZE,
    height: DEFAULT_FLOATING_BUTTON_SIZE,
  })
  const dragOffsetRef = useRef({ x: 0, y: 0 })
  const hasDraggedRef = useRef(false)
  const dragStartRef = useRef({ x: 0, y: 0 })
  const widgetDragOffsetRef = useRef({ x: 0, y: 0 })
  const widgetDragStartRef = useRef({ x: 0, y: 0 })
  const widgetHasDraggedRef = useRef(false)
  const lastWidgetPositionRef = useRef(null)
  const resizeStartRef = useRef({ width: 0, height: 0, left: 0, top: 0, right: 0, bottom: 0, x: 0, y: 0 })
  const resizeDirectionRef = useRef("se")
  const chatContainerRef = useRef(null)
  const initializedSessionRef = useRef(false)
  const wasSendingRef = useRef(false)
  const sortedRooms = sortRoomsByRecentQuestion(rooms, messagesByRoom)

  const isChatPage =
    typeof location?.pathname === "string" && location.pathname.startsWith("/assistant")

  const { isAttentionTooltipVisible, attentionTooltipText } = useAttentionTooltip({
    isOpen,
    isChatPage,
  })

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen || typeof window === "undefined") return
    if (widgetPosition.x !== null && widgetPosition.y !== null) return

    const offset = 16
    setWidgetPosition(
      clampPosition(
        window.innerWidth - size.width - offset,
        window.innerHeight - size.height - offset,
        size.width,
        size.height,
      ),
    )
  }, [isOpen, size.height, size.width, widgetPosition.x, widgetPosition.y])

  useEffect(() => {
    if (!isOpen || typeof document === "undefined") return

    const handlePointerDown = (event) => {
      const target = event.target
      const targetElement = target instanceof Element ? target : target?.parentElement
      const eventPath = typeof event.composedPath === "function" ? event.composedPath() : []
      const clickedInsideWidget =
        chatContainerRef.current &&
        (chatContainerRef.current.contains(targetElement) || eventPath.includes(chatContainerRef.current))
      if (clickedInsideWidget) return

      const hasPortalTarget =
        eventPath.some(
          (node) => node instanceof Element && node.hasAttribute?.("data-chat-widget-portal"),
        ) || targetElement?.closest?.("[data-chat-widget-portal]")
      if (hasPortalTarget) return

      if (chatContainerRef.current && !chatContainerRef.current.contains(targetElement)) {
        if (typeof window !== "undefined") {
          const rect = chatContainerRef.current?.getBoundingClientRect()
          if (rect) {
            const { width: buttonWidth, height: buttonHeight } = floatingButtonSizeRef.current
            setButtonPosition(
              clampPosition(
                rect.right - buttonWidth,
                rect.bottom - buttonHeight,
                buttonWidth,
                buttonHeight,
              ),
            )
          }
        }
        setIsWidgetDragging(false)
        setIsResizing(false)
        setIsOpen(false)
      }
    }

    document.addEventListener("pointerdown", handlePointerDown, true)
    return () => document.removeEventListener("pointerdown", handlePointerDown, true)
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return

    const ensureWidgetWithinBounds = () => {
      if (isMaximized) {
        if (typeof window === "undefined") return
        const nextSize = { width: window.innerWidth, height: window.innerHeight }
        sizeRef.current = nextSize
        setSize(nextSize)
        setWidgetPosition({ x: 0, y: 0 })
        return
      }

      setSize((prevSize) => {
        const nextSize = clampSize(prevSize.width, prevSize.height)
        sizeRef.current = nextSize
        setWidgetPosition((prevPosition) => {
          if (prevPosition.x === null || prevPosition.y === null) return prevPosition
          const nextPosition = clampPosition(
            prevPosition.x,
            prevPosition.y,
            nextSize.width,
            nextSize.height,
          )
          if (nextPosition.x === prevPosition.x && nextPosition.y === prevPosition.y) {
            return prevPosition
          }
          return nextPosition
        })
        return nextSize
      })
    }

    ensureWidgetWithinBounds()

    if (typeof window === "undefined") return

    window.addEventListener("resize", ensureWidgetWithinBounds)
    return () => window.removeEventListener("resize", ensureWidgetWithinBounds)
  }, [isMaximized, isOpen])

  useEffect(() => {
    if (!isResizing) return

    const handlePointerMove = (event) => {
      const direction = resizeDirectionRef.current || "se"
      const deltaX = event.clientX - resizeStartRef.current.x
      const deltaY = event.clientY - resizeStartRef.current.y
      const isResizingWest = direction.includes("w")
      const isResizingNorth = direction.includes("n")
      const isResizingEast = direction.includes("e")
      const isResizingSouth = direction.includes("s")

      let nextWidth = resizeStartRef.current.width
      let nextHeight = resizeStartRef.current.height

      if (isResizingEast) nextWidth = resizeStartRef.current.width + deltaX
      if (isResizingWest) nextWidth = resizeStartRef.current.width - deltaX
      if (isResizingSouth) nextHeight = resizeStartRef.current.height + deltaY
      if (isResizingNorth) nextHeight = resizeStartRef.current.height - deltaY

      const nextSize = clampSize(nextWidth, nextHeight)
      const prevSize = sizeRef.current
      const sizeUnchanged =
        nextSize.width === prevSize.width && nextSize.height === prevSize.height
      if (sizeUnchanged) return
      const nextPosition = clampPosition(
        isResizingWest ? resizeStartRef.current.right - nextSize.width : resizeStartRef.current.left,
        isResizingNorth ? resizeStartRef.current.bottom - nextSize.height : resizeStartRef.current.top,
        nextSize.width,
        nextSize.height,
      )

      sizeRef.current = nextSize
      setSize(nextSize)
      setWidgetPosition(nextPosition)
    }

    const handlePointerUp = () => {
      resizeDirectionRef.current = "se"
      setIsResizing(false)
    }

    document.addEventListener("pointermove", handlePointerMove)
    document.addEventListener("pointerup", handlePointerUp)
    document.addEventListener("pointercancel", handlePointerUp)
    return () => {
      document.removeEventListener("pointermove", handlePointerMove)
      document.removeEventListener("pointerup", handlePointerUp)
      document.removeEventListener("pointercancel", handlePointerUp)
    }
  }, [isResizing])

  useEffect(() => {
    if (!isWidgetDragging) return

    const handlePointerMove = (event) => {
      if (!chatContainerRef.current) return

      const rect = chatContainerRef.current.getBoundingClientRect()
      const nextPosition = clampPosition(
        event.clientX - widgetDragOffsetRef.current.x,
        event.clientY - widgetDragOffsetRef.current.y,
        rect.width,
        rect.height,
      )

      if (
        !widgetHasDraggedRef.current &&
        (Math.abs(event.clientX - widgetDragStartRef.current.x) > 2 ||
          Math.abs(event.clientY - widgetDragStartRef.current.y) > 2)
      ) {
        widgetHasDraggedRef.current = true
      }

      setWidgetPosition(nextPosition)
    }

    const handlePointerUp = () => {
      setIsWidgetDragging(false)
    }

    document.addEventListener("pointermove", handlePointerMove)
    document.addEventListener("pointerup", handlePointerUp)
    document.addEventListener("pointercancel", handlePointerUp)
    return () => {
      document.removeEventListener("pointermove", handlePointerMove)
      document.removeEventListener("pointerup", handlePointerUp)
      document.removeEventListener("pointercancel", handlePointerUp)
    }
  }, [isWidgetDragging])

  useEffect(() => {
    if (
      typeof window === "undefined" ||
      buttonPosition.x !== null ||
      buttonPosition.y !== null ||
      !floatingButtonRef.current
    ) {
      return
    }

    const rect = floatingButtonRef.current.getBoundingClientRect()
    floatingButtonSizeRef.current = { width: rect.width, height: rect.height }
    const offset = 16
    setButtonPosition({
      x: window.innerWidth - rect.width - offset - 32,
      y: window.innerHeight - rect.height - offset - 5,
    })
  }, [buttonPosition.x, buttonPosition.y])

  useEffect(() => {
    if (initializedSessionRef.current) return
    const hasPreviousConversation = Object.values(messagesByRoom || {}).some((roomMessages) =>
      Array.isArray(roomMessages) && roomMessages.some((message) => message?.role === "user")
    )
    const hasExistingRooms = Array.isArray(rooms) && rooms.length > 0
    if (!hasPreviousConversation && !hasExistingRooms) {
      createRoom("새 대화")
    }
    initializedSessionRef.current = true
  }, [createRoom, messagesByRoom, rooms])

  useEffect(() => {
    if (!isOpen) {
      wasSendingRef.current = isSending
      return
    }

    if (!isSending && wasSendingRef.current && inputRef.current) {
      inputRef.current.focus()
    }

    wasSendingRef.current = isSending
  }, [isSending, isOpen])

  if (isChatPage) {
    return null
  }

  const closeWidget = () => {
    if (typeof window !== "undefined") {
      const rect = chatContainerRef.current?.getBoundingClientRect()
      if (rect) {
        const { width: buttonWidth, height: buttonHeight } = floatingButtonSizeRef.current
        const nextButtonPosition = clampPosition(
          rect.right - buttonWidth,
          rect.bottom - buttonHeight,
          buttonWidth,
          buttonHeight,
        )
        setButtonPosition(nextButtonPosition)
      }
    }
    setIsWidgetDragging(false)
    setIsResizing(false)
    setIsOpen(false)
  }

  const focusInput = () => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }

  const handleInputChange = (event) => {
    setInput(event.target.value)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!input.trim() || isSending) return
    try {
      await sendMessage(input)
      setInput("")
    } finally {
      focusInput()
    }
  }

  const resizeWidget = (nextSize) => {
    sizeRef.current = nextSize
    setSize(nextSize)
    setWidgetPosition((prevPosition) => {
      if (typeof window === "undefined") return prevPosition
      const offset = 16
      if (prevPosition.x === null || prevPosition.y === null) {
        return clampPosition(
          window.innerWidth - nextSize.width - offset,
          window.innerHeight - nextSize.height - offset,
          nextSize.width,
          nextSize.height,
        )
      }
      return clampPosition(prevPosition.x, prevPosition.y, nextSize.width, nextSize.height)
    })
  }

  const handleOpenFullChat = () => {
    if (isMaximized) return
    if (widgetPosition.x !== null && widgetPosition.y !== null) {
      lastWidgetPositionRef.current = { x: widgetPosition.x, y: widgetPosition.y }
    }
    setIsMaximized(true)
    if (typeof window === "undefined") return
    const nextSize = { width: window.innerWidth, height: window.innerHeight }
    sizeRef.current = nextSize
    setSize(nextSize)
    setWidgetPosition({ x: 0, y: 0 })
  }

  const handleRestoreDefaultSize = () => {
    const nextSize = clampSize(DEFAULT_CHAT_WIDTH, DEFAULT_CHAT_HEIGHT)
    setIsMaximized(false)
    resizeWidget(nextSize)
    if (lastWidgetPositionRef.current) {
      setWidgetPosition(
        clampPosition(
          lastWidgetPositionRef.current.x,
          lastWidgetPositionRef.current.y,
          nextSize.width,
          nextSize.height,
        ),
      )
    }
  }

  const handleFloatingButtonPointerDown = (event) => {
    if (!floatingButtonRef.current) return

    const rect = floatingButtonRef.current.getBoundingClientRect()
    dragOffsetRef.current = {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    }
    dragStartRef.current = { x: event.clientX, y: event.clientY }
    hasDraggedRef.current = false
    setIsDragging(true)
    floatingButtonRef.current.setPointerCapture?.(event.pointerId)
  }

  const handleFloatingButtonPointerMove = (event) => {
    if (!isDragging || !floatingButtonRef.current) return

    const rect = floatingButtonRef.current.getBoundingClientRect()
    const nextPosition = clampPosition(
      event.clientX - dragOffsetRef.current.x,
      event.clientY - dragOffsetRef.current.y,
      rect.width,
      rect.height,
    )

    if (
      !hasDraggedRef.current &&
      (Math.abs(event.clientX - dragStartRef.current.x) > 2 ||
        Math.abs(event.clientY - dragStartRef.current.y) > 2)
    ) {
      hasDraggedRef.current = true
    }

    setButtonPosition(nextPosition)
  }

  const handleFloatingButtonPointerUp = (event) => {
    if (!isDragging) return
    setIsDragging(false)
    floatingButtonRef.current?.releasePointerCapture(event.pointerId)
  }

  const handleFloatingButtonClick = () => {
    if (hasDraggedRef.current) {
      hasDraggedRef.current = false
      return
    }

    const rect = floatingButtonRef.current?.getBoundingClientRect()
    if (rect) {
      setWidgetPosition(
        clampPosition(
          rect.right - size.width,
          rect.bottom - size.height,
          size.width,
          size.height,
        ),
      )
    } else if (typeof window !== "undefined") {
      const offset = 16
      setWidgetPosition(
        clampPosition(
          window.innerWidth - size.width - offset,
          window.innerHeight - size.height - offset,
          size.width,
          size.height,
        ),
      )
    }
    setIsOpen(true)
  }

  const handleWidgetHeaderPointerDown = (event) => {
    if (!chatContainerRef.current || isResizing || isMaximized) return

    const target = event.target
    const targetElement = target instanceof Element ? target : target?.parentElement
    const isInteractiveElement = targetElement?.closest?.(
      "button, a, input, textarea, select, [data-chat-widget-no-drag=\"true\"]",
    )
    if (isInteractiveElement) return

    event.preventDefault()
    const rect = chatContainerRef.current.getBoundingClientRect()
    widgetDragOffsetRef.current = {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    }
    widgetDragStartRef.current = { x: event.clientX, y: event.clientY }
    widgetHasDraggedRef.current = false
    setIsWidgetDragging(true)
  }

  const handleResizePointerDown = (direction) => (event) => {
    event.preventDefault()
    event.stopPropagation()
    if (isMaximized) return
    if (!chatContainerRef.current) return

    const rect = chatContainerRef.current.getBoundingClientRect()
    resizeDirectionRef.current = direction
    resizeStartRef.current = {
      width: rect.width,
      height: rect.height,
      left: rect.left,
      top: rect.top,
      right: rect.right,
      bottom: rect.bottom,
      x: event.clientX,
      y: event.clientY,
    }
    event.currentTarget.setPointerCapture?.(event.pointerId)
    setIsResizing(true)
  }

  if (!isOpen) {
    return (
      <ChatWidgetLauncher
        buttonPosition={buttonPosition}
        onPointerDown={handleFloatingButtonPointerDown}
        onPointerMove={handleFloatingButtonPointerMove}
        onPointerUp={handleFloatingButtonPointerUp}
        onClick={handleFloatingButtonClick}
        floatingButtonRef={floatingButtonRef}
        isAttentionTooltipVisible={isAttentionTooltipVisible}
        attentionTooltipText={attentionTooltipText}
      />
    )
  }

  return (
    <ChatWidgetPanel
      containerRef={chatContainerRef}
      widgetPosition={widgetPosition}
      size={size}
      isMaximized={isMaximized}
      onResizePointerDown={handleResizePointerDown}
      onHeaderPointerDown={handleWidgetHeaderPointerDown}
      isSidebarOpen={isSidebarOpen}
      onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
      ragSettings={ragSettings}
      rooms={rooms}
      sortedRooms={sortedRooms}
      activeRoomId={activeRoomId}
      onSelectRoom={selectRoom}
      onDeleteRoom={removeRoom}
      onCreateRoom={createRoom}
      messages={messages}
      isSending={isSending}
      availableMailboxes={availableMailboxes}
      errorMessage={errorMessage}
      onClearError={clearError}
      inputRef={inputRef}
      inputValue={input}
      onInputChange={handleInputChange}
      onSubmit={handleSubmit}
      onOpenFullChat={handleOpenFullChat}
      onRestoreDefaultSize={handleRestoreDefaultSize}
      onClose={closeWidget}
    />
  )
}
