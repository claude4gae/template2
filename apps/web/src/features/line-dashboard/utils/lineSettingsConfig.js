export const DUPLICATE_MESSAGE = "이미 등록된 스텝입니다. 다른 스텝을 입력해주세요."
export const DUPLICATE_TARGET_MESSAGE = "이미 등록된 알림 Target입니다. 다른 Target을 입력해주세요."
export const DUPLICATE_TARGET_MAPPING_MESSAGE = "이미 등록된 지정 조합입니다. 다른 조합을 입력해주세요."
export const MAX_FIELD_LENGTH = 50
export const MAX_JIRA_KEY_LENGTH = 64
export const MAX_NEED_TO_SEND_KEYWORD_LENGTH = 64
export const MAX_TARGET_FIELD_LENGTH = 64
export const DEFAULT_CHANNEL_ENABLED = { jira: true, messenger: true, mail: true }
export const DEFAULT_NEED_TO_SEND_RULE = { commentKeyword: "", enabled: false, ignoreSampleType: false }
export const DEFAULT_TEMPLATE_KEYS = { jira: "common", messenger: "common", mail: "common" }
export const RECIPIENT_CHANNELS = [
  {
    channel: "messenger",
    title: "메신저 수신인",
    contactField: "knox_id",
    countLabel: "메신저 수신인",
    emptyText: "등록된 메신저 수신인이 없습니다.",
    loadingText: "메신저 수신인을 불러오는 중입니다.",
    permissionErrorText: "메신저 수신인 변경 권한이 없습니다.",
    saveDescription: "메신저 수신인 목록이 저장되었습니다.",
  },
  {
    channel: "mail",
    title: "메일 수신인",
    contactField: "email",
    countLabel: "메일 수신인",
    emptyText: "등록된 메일 수신인이 없습니다.",
    loadingText: "메일 수신인을 불러오는 중입니다.",
    permissionErrorText: "메일 수신인 변경 권한이 없습니다.",
    saveDescription: "메일 수신인 목록이 저장되었습니다.",
  },
]
export const RECIPIENT_CHANNEL_CONFIG = RECIPIENT_CHANNELS.reduce((acc, config) => {
  acc[config.channel] = config
  return acc
}, {})
