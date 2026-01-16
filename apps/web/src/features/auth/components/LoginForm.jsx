// src/features/auth/components/LoginForm.jsx
// 로그인 화면에서 사용하는 폼 UI와 상호작용 로직을 담당합니다.
// - 상태/비즈니스 로직은 useAuth 훅에서 받아오고, 여기서는 UI에만 집중합니다.

import { useEffect, useRef, useState } from "react"
import { useSearchParams } from "react-router-dom"

import { cn } from "@/lib/utils"
import { useTheme } from "@/lib/theme"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldSeparator,
} from "@/components/ui/field"

import { useAuth } from "../hooks/useAuth"

export function LoginForm({
  className,
  ...props
}) {
  const [isLoading, setIsLoading] = useState(false)
  const { theme = "system", systemTheme } = useTheme()
  const { login, config } = useAuth()
  const [searchParams] = useSearchParams()
  const nextPath = searchParams?.get("next") || "/"
  const autoLoginTriggeredRef = useRef(false)

  // provider 설정이 없는 경우를 대비해 버튼을 비활성화합니다.
  const providerAvailable = config?.providerConfigured !== false
  const resolvedTheme = theme === "system" ? systemTheme : theme
  const logoSrc = resolvedTheme === "dark" ? "/images/Samsung_WHITE.png" : "/images/Samsung_BLUE.png"

  const handleLoginClick = async () => {
    if (!providerAvailable) return
    try {
      setIsLoading(true)
      await login({ next: nextPath })
    } finally {
      setIsLoading(false)
    }
  }

  // 로그인 페이지 진입 시 버튼 클릭 없이 자동으로 로그인 시도
  useEffect(() => {
    if (!providerAvailable) return
    if (autoLoginTriggeredRef.current) return
    autoLoginTriggeredRef.current = true
    const autoLogin = async () => {
      try {
        setIsLoading(true)
        await login({ next: nextPath })
      } finally {
        setIsLoading(false)
      }
    }
    autoLogin()
  }, [login, nextPath, providerAvailable])

  return (
    <div className={cn("flex flex-col gap-3", className)} {...props}>
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Welcome</CardTitle>
          <CardDescription>Login with SSO</CardDescription>
        </CardHeader>
        <CardContent>
          <form>
            <FieldGroup>
              <Field>
                <FieldLabel className="sr-only">SSO 로그인</FieldLabel>
                <Button
                  variant="outline"
                  type="button"
                  onClick={handleLoginClick}
                  disabled={isLoading || !providerAvailable}
                >
                  <img
                    src={logoSrc}
                    alt="Samsung logo"
                    className="mr-2 h-5 w-auto"
                  />
                </Button>
              </Field>
              <FieldSeparator className="sr-only" />
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
      <FieldDescription className="px-6 text-center">
        By clicking continue, you agree to our <a href="#">Terms of Service</a>{" "}
        and <a href="#">Privacy Policy</a>.
      </FieldDescription>
    </div>
  )
}
