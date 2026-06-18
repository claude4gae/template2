// 파일 경로: src/features/auth/components/RequireAuth.jsx
// 보호된 페이지를 렌더링하기 전에 인증 여부를 확인하는 가드 컴포넌트입니다.
// - 인증 상태는 useAuth 훅에서 가져오고,
// - 로딩/비인증 상태일 때는 CenteredPage 레이아웃으로 안내 메시지를 보여줍니다.

import { useEffect } from "react"
import { useLocation, useNavigate } from "react-router-dom"

import { Spinner } from "@/components/ui/spinner"
import { CenteredPage } from "./CenteredPage"
import { useAuth } from "../hooks/useAuth"

/**
 * 현재 URL을 기반으로 로그인 후 돌아올 next 파라미터 문자열을 생성합니다.
 * 초보자 팁: pathname + searchParams를 조합해 "원래 보고 있던 페이지" 정보를 유지합니다.
 */
function buildNextParam(location) {
  if (!location?.pathname) {
    return ""
  }

  if (location.search) {
    return `${location.pathname}${location.search}`
  }

  return location.pathname
}

export function RequireAuth({ children }) {
  const { user, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const nextParam = buildNextParam(location)

  useEffect(() => {
    if (!isLoading && !user) {
      const search = nextParam && nextParam !== "/" ? `?next=${encodeURIComponent(nextParam)}` : ""
      navigate(`/login${search}`, { replace: true })
    }
  }, [isLoading, location.pathname, location.search, navigate, nextParam, user])

  if (isLoading && !user) {
    return (
      <CenteredPage>
        <div className="flex flex-col items-center gap-3">
          <Spinner className="size-8 text-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </CenteredPage>
    )
  }

  if (!user) {
    return (
      <CenteredPage>
        <div className="flex flex-col items-center gap-3">
          <Spinner className="size-8 text-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </CenteredPage>
    )
  }

  return children
}
