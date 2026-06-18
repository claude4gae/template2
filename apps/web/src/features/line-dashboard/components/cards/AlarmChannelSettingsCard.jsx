import { IconDeviceFloppy } from "@tabler/icons-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const ALARM_CHANNELS = [
  { key: "jira", label: "Jira", description: "Jira 채널" },
  { key: "messenger", label: "Teams", description: "메신저 채널" },
  { key: "mail", label: "Mail", description: "메일 채널" },
]

function getTemplateOptionsForChannel(options, channelKey, selectedValue) {
  const channelOptions = Array.isArray(options?.[channelKey]) ? options[channelKey] : []
  if (!selectedValue || channelOptions.some((option) => option.key === selectedValue)) {
    return channelOptions
  }
  return [{ key: selectedValue, label: selectedValue }, ...channelOptions]
}

export function AlarmChannelSettingsCard({
  selectedUserSdwtProd,
  jiraKeyDraft,
  channelEnabledDraft,
  templateKeyDraft,
  templateOptions,
  maxJiraKeyLength,
  jiraKeyFormError,
  jiraKeyError,
  isJiraKeyLoading,
  isSavingJiraKey,
  canManage,
  onJiraKeyDraftChange,
  onChannelEnabledChange,
  onTemplateKeyChange,
  onSaveJiraKey,
}) {
  const showPermissionNotice = Boolean(selectedUserSdwtProd && !canManage)

  return (
    <div className="flex min-w-0 flex-col gap-2 overflow-hidden rounded-lg border bg-background p-4 shadow-sm">
      <div className="shrink-0 space-y-1">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-base font-medium">알람 채널 설정</h2>
            {showPermissionNotice ? (
              <Badge variant="secondary" className="mt-1 shrink-0 text-[10px]">
                스태프 권한이 필요
              </Badge>
            ) : null}
          </div>
          <Button
            type="submit"
            form="alarm-channel-settings-form"
            size="sm"
            variant="outline"
            disabled={!selectedUserSdwtProd || isJiraKeyLoading || isSavingJiraKey || !canManage}
            className="h-8 shrink-0 gap-1 px-2 text-xs"
          >
            <IconDeviceFloppy className="size-3.5" />
            설정 저장
          </Button>
        </div>
      </div>

      {jiraKeyFormError ? (
        <p className="shrink-0 text-xs text-destructive" role="alert">
          {jiraKeyFormError}
        </p>
      ) : jiraKeyError ? (
        <p className="shrink-0 text-xs text-destructive" role="alert">
          {jiraKeyError}
        </p>
      ) : null}

      <form id="alarm-channel-settings-form" className="flex min-h-0 flex-col gap-2" onSubmit={onSaveJiraKey}>
        <div className="min-h-0 rounded-md border p-1.5">
          <div className="grid gap-1.5">
            {ALARM_CHANNELS.map((channel) => {
              const isEnabled = Boolean(channelEnabledDraft[channel.key])
              const checkboxId = `alarm-channel-${channel.key}-enabled`
              const isJiraChannel = channel.key === "jira"
              const selectedTemplateKey = templateKeyDraft?.[channel.key] || ""
              const channelTemplateOptions = getTemplateOptionsForChannel(
                templateOptions,
                channel.key,
                selectedTemplateKey,
              )
              return (
                <div
                  key={channel.key}
                  className="flex min-w-0 items-center gap-3 rounded-md bg-muted/40 px-2 py-2"
                >
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <div className="flex min-w-0 items-center gap-3">
                      <Checkbox
                        id={checkboxId}
                        checked={isEnabled}
                        disabled={!selectedUserSdwtProd || isJiraKeyLoading || isSavingJiraKey || !canManage}
                        onCheckedChange={(checked) => onChannelEnabledChange(channel.key, checked === true)}
                      />
                      <label className="min-w-0 cursor-pointer" htmlFor={checkboxId}>
                        <p className="text-xs font-medium">{channel.label}</p>
                        <p className="truncate text-[11px] text-muted-foreground">{channel.description}</p>
                      </label>
                    </div>
                  </div>

                  <div className="flex shrink-0 items-center gap-2">
                    {isJiraChannel ? (
                      <Input
                        id="alarm-channel-jira-key-input"
                        value={jiraKeyDraft}
                        onChange={(event) => onJiraKeyDraftChange(event.target.value)}
                        placeholder="Jira project key 입력"
                        maxLength={maxJiraKeyLength}
                        disabled={!selectedUserSdwtProd || isJiraKeyLoading || isSavingJiraKey || !canManage}
                        className="h-8 w-36 shrink-0 text-xs"
                      />
                    ) : null}
                    <Select
                      value={selectedTemplateKey}
                      onValueChange={(value) => onTemplateKeyChange(channel.key, value)}
                      disabled={
                        !selectedUserSdwtProd ||
                        isJiraKeyLoading ||
                        isSavingJiraKey ||
                        !canManage ||
                        channelTemplateOptions.length === 0
                      }
                    >
                      <SelectTrigger
                        aria-label={`${channel.label} 템플릿 선택`}
                        size="sm"
                        className="h-8 w-40 text-xs"
                      >
                        <SelectValue placeholder="템플릿 선택" />
                      </SelectTrigger>
                      <SelectContent align="end">
                        {channelTemplateOptions.map((option) => (
                          <SelectItem key={option.key} value={option.key}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Badge variant={isEnabled ? "default" : "secondary"} className="shrink-0 text-[10px]">
                    {isEnabled ? "활성" : "비활성"}
                  </Badge>
                </div>
              )
            })}
          </div>
        </div>
      </form>
    </div>
  )
}
