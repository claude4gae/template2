import {
  ActivityIcon,
  BarChart3Icon,
  BotIcon,
  ClipboardListIcon,
  LayoutGridIcon,
  MailIcon,
  MessageSquareIcon,
  SettingsIcon,
  ShieldCheckIcon,
  SparklesIcon,
  StoreIcon,
  UsersIcon,
} from "lucide-react"

import portalLogoPng from "../../assets/images/logo.png"

export const PORTAL_BRAND_KEY = "portal"

export const PORTAL_BRAND_REGISTRY = Object.freeze({
  [PORTAL_BRAND_KEY]: {
    key: PORTAL_BRAND_KEY,
    name: "Etch AX Portal",
    pathPrefixes: ["/"],
    mark: {
      type: "image",
      src: portalLogoPng,
      alt: "Etch AX Portal",
    },
  },
  appstore: {
    key: "appstore",
    name: "Appstore",
    pathPrefixes: ["/appstore"],
    mark: {
      type: "icon",
      icon: StoreIcon,
    },
  },
  "line-dashboard": {
    key: "line-dashboard",
    name: "ESOP Dashboard",
    pathPrefixes: ["/ESOP_Dashboard", "/esop_dashboard"],
    mark: {
      type: "icon",
      icon: BarChart3Icon,
    },
  },
  observer: {
    key: "observer",
    name: "Observer",
    pathPrefixes: ["/observer"],
    mark: {
      type: "icon",
      icon: ClipboardListIcon,
    },
  },
  emails: {
    key: "emails",
    name: "메일함",
    pathPrefixes: ["/emails"],
    mark: {
      type: "icon",
      icon: MailIcon,
    },
  },
  "fdc-trend": {
    key: "fdc-trend",
    name: "L0 Spider",
    pathPrefixes: ["/fdc_trend"],
    mark: {
      type: "icon",
      icon: ActivityIcon,
    },
  },
  "l3-spider": {
    key: "l3-spider",
    name: "L3 Spider",
    pathPrefixes: ["/l3_spider"],
    mark: {
      type: "icon",
      icon: SparklesIcon,
    },
  },
  "pm-comparison": {
    key: "pm-comparison",
    name: "PM SPIDER",
    pathPrefixes: ["/pm-comparison"],
    mark: {
      type: "icon",
      icon: ShieldCheckIcon,
    },
  },
  "access-stats": {
    key: "access-stats",
    name: "접속 현황",
    pathPrefixes: ["/access-stats"],
    mark: {
      type: "icon",
      icon: LayoutGridIcon,
    },
  },
  teamstaff: {
    key: "teamstaff",
    name: "Team",
    pathPrefixes: ["/teamstaff"],
    mark: {
      type: "icon",
      icon: UsersIcon,
    },
  },
  voc: {
    key: "voc",
    name: "VoE",
    pathPrefixes: ["/voc"],
    mark: {
      type: "icon",
      icon: MessageSquareIcon,
    },
  },
  settings: {
    key: "settings",
    name: "Settings",
    pathPrefixes: ["/settings"],
    mark: {
      type: "icon",
      icon: SettingsIcon,
    },
  },
  assistant: {
    key: "assistant",
    name: "Assistant",
    pathPrefixes: ["/assistant"],
    mark: {
      type: "icon",
      icon: BotIcon,
    },
  },
})

function normalizePathname(pathname) {
  if (typeof pathname !== "string" || !pathname.trim()) return "/"
  return pathname.startsWith("/") ? pathname : `/${pathname}`
}

function matchesPathPrefix(pathname, pathPrefix) {
  if (pathPrefix === "/") return pathname === "/"
  return pathname === pathPrefix || pathname.startsWith(`${pathPrefix}/`)
}

export function resolvePortalBrand(pathname) {
  const normalizedPathname = normalizePathname(pathname)
  const brands = Object.values(PORTAL_BRAND_REGISTRY)
    .filter((brand) => brand.key !== PORTAL_BRAND_KEY)
    .sort((left, right) => {
      const leftLength = Math.max(...left.pathPrefixes.map((pathPrefix) => pathPrefix.length))
      const rightLength = Math.max(...right.pathPrefixes.map((pathPrefix) => pathPrefix.length))
      return rightLength - leftLength
    })

  return (
    brands.find((brand) =>
      brand.pathPrefixes.some((pathPrefix) => matchesPathPrefix(normalizedPathname, pathPrefix)),
    ) ?? PORTAL_BRAND_REGISTRY[PORTAL_BRAND_KEY]
  )
}
