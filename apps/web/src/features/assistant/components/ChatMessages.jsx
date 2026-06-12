import { useEffect, useRef } from "react"
import { Link, useNavigate } from "react-router-dom"

import { Badge } from "@/components/ui/badge"

import { AssistantStatusIndicator } from "./AssistantStatusIndicator"
import { formatAssistantMessage } from "../utils/formatAssistantMessage"
import { buildEmailSourceUrl } from "../utils/buildEmailSourceUrl"

export function ChatMessages({
  messages = [],
  isSending,
  fillBubbles = false,
  availableMailboxes = [],
}) {
  const messagesEndRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isSending])

  const handleEmailSourceClick = (event) => {
    const target = event?.target
    if (!(target instanceof Element)) return
    const anchor = target.closest?.("a[data-email-source]")
    const href = anchor?.getAttribute?.("href")
    if (!href) return
    event.preventDefault()
    navigate(href)
  }

  return (
    <div className="flex-1 min-h-0 space-y-3 overflow-y-auto px-4 py-3">
      {messages.map((message) => {
        const isUser = message.role === "user"
        const sources = Array.isArray(message.sources) ? message.sources : []
        const messageMailbox =
          typeof message.userSdwtProd === "string" ? message.userSdwtProd.trim() : ""
        const baseBubbleClasses = [
          "max-w-[90%]",
          "rounded-2xl",
          "px-4",
          "py-2",
          "text-sm",
          "shadow-sm",
        ].filter(Boolean)

        return (
          <div
            key={message.id}
            className={["flex", isUser ? "justify-end" : "justify-start"].join(" ")}
          >
            {isUser ? (
              <pre
                className={[
                  ...baseBubbleClasses,
                  "m-0 whitespace-pre-wrap break-words",
                  "bg-primary text-primary-foreground font-sans leading-relaxed text-xs",
                ].join(" ")}
              >
                {message.content}
              </pre>
            ) : (
              <div className={["space-y-2", fillBubbles ? "w-full" : null].filter(Boolean).join(" ")}>
                <div
                  className={[
                    ...baseBubbleClasses,
                    "bg-muted text-foreground leading-relaxed break-words space-y-2",
                    "[&_p]:my-2",
                    "[&_ul]:list-disc [&_ol]:list-decimal [&_ul]:pl-5 [&_ol]:pl-5 [&_li]:my-1",
                    "[&_table]:w-full [&_table]:border-collapse [&_th]:border [&_td]:border [&_th]:bg-muted/80 [&_th]:px-3 [&_th]:py-2 [&_td]:px-3 [&_td]:py-2 [&_tr:nth-child(even)]:bg-muted/50",
                    "[&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5",
                    "[&_pre]:rounded-lg [&_pre]:bg-muted [&_pre]:p-3 [&_pre]:overflow-x-auto",
                    "[&_a[data-email-source]]:inline-flex [&_a[data-email-source]]:items-center [&_a[data-email-source]]:rounded-full [&_a[data-email-source]]:border [&_a[data-email-source]]:border-border [&_a[data-email-source]]:bg-background [&_a[data-email-source]]:px-2 [&_a[data-email-source]]:py-0.5 [&_a[data-email-source]]:text-xs [&_a[data-email-source]]:font-medium [&_a[data-email-source]]:text-foreground [&_a[data-email-source]]:no-underline [&_a[data-email-source]]:hover:bg-muted",
                  ].join(" ")}
                >
                  <div
                    onClick={handleEmailSourceClick}
                    dangerouslySetInnerHTML={{
                      __html: formatAssistantMessage(
                        message.content,
                        sources,
                        messageMailbox,
                        availableMailboxes,
                      ),
                    }}
                  />
                  {sources.length > 0 ? (
                    <div className="flex flex-wrap items-center gap-1 pt-1">
                      {sources.map((source) => (
                        <Badge
                          key={`${message.id}-${source.docId}`}
                          asChild
                          variant="outline"
                          className="max-w-60"
                        >
                          <Link
                            to={buildEmailSourceUrl(source.docId, messageMailbox, {
                              availableMailboxes,
                            })}
                          >
                            <span className="truncate">{source.title || source.docId}</span>
                          </Link>
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            )}
          </div>
        )
      })}

      <AssistantStatusIndicator isSending={isSending} />
      <div ref={messagesEndRef} />
    </div>
  )
}
