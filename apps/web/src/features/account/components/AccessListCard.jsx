import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

import {
  ACCESS_ROLE_LABELS,
  ACCESS_ROLE_VARIANTS,
  formatAccountDateValue,
  resolveAccessRole,
} from "../utils/accountOverview"

function AccessList({ items }) {
  if (!items?.length) {
    return <p className="text-sm text-muted-foreground">권한이 없습니다.</p>
  }

  return (
    <div className="grid gap-2">
      {items.map((item) => {
        const role = resolveAccessRole(item.role)
        return (
          <div
            key={`${item.userSdwtProd}-${item.source}`}
            className="flex flex-col gap-1 rounded-md border px-3 py-2"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-medium">{item.userSdwtProd}</span>
                {item.source === "self" ? (
                  <Badge variant="secondary">내 소속</Badge>
                ) : (
                  <Badge variant="outline">부여됨</Badge>
                )}
              </div>
              <Badge variant={ACCESS_ROLE_VARIANTS[role]}>{ACCESS_ROLE_LABELS[role]}</Badge>
            </div>
            {item.grantedAt ? (
              <span className="text-xs text-muted-foreground">
                부여 시각: {formatAccountDateValue(item.grantedAt)}
              </span>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}

export function AccessListCard({ data }) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-1">
        <CardTitle>메일함 접근</CardTitle>
        <CardDescription>
          user_sdwt_prod 단위로 메일함과 RAG 인덱스 접근 권한을 확인하세요.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 grid-cols-2 items-stretch">
        <div className="flex h-full min-h-0 flex-col gap-2">
          <h3 className="text-sm font-semibold text-foreground">접근 가능 목록</h3>
          <div className="flex-1 min-h-0">
            <AccessList items={data?.accessibleUserSdwtProds} />
          </div>
        </div>
        <div className="flex h-full min-h-0 flex-col gap-2">
          <h3 className="text-sm font-semibold text-foreground">관리 가능한 그룹</h3>
          <div className="flex-1 min-h-0 rounded-md border px-3 py-2">
            {data?.manageableUserSdwtProds?.length ? (
              <div className="flex flex-wrap gap-2">
                {data.manageableUserSdwtProds.map((item) => (
                  <Badge key={item} variant="secondary">
                    {item}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">관리 권한이 없습니다.</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
