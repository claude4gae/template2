import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/common"

const SOURCE_LABELS = {
  self: "내 소속",
  grant: "부여됨",
  privileged: "관리자 전체",
  unknown: "기타",
}

function formatDate(value) {
  if (!value) return "-"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString("ko-KR")
}

export function MailboxAccessCard({ mailboxes }) {
  if (!mailboxes?.length) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-2">
          <CardTitle>메일함 접근 현황</CardTitle>
          <CardDescription>접근 가능한 메일함의 상세 상태를 확인합니다.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">접근 가능한 메일함이 없습니다.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle>메일함 접근 현황</CardTitle>
        <CardDescription>접근 가능한 메일함의 상세 상태를 확인합니다.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3">
        <div className="max-h-48 min-h-0 overflow-y-auto rounded-lg border">
          <Table stickyHeader>
            <TableHeader>
              <TableRow>
                <TableHead>메일함</TableHead>
                <TableHead>접근 경로</TableHead>
                <TableHead>권한</TableHead>
                <TableHead>멤버 수</TableHead>
                <TableHead>내 메일 수</TableHead>
                <TableHead>부여 시각</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mailboxes.map((mailbox) => (
                <TableRow key={mailbox.userSdwtProd}>
                  <TableCell className="font-medium">{mailbox.userSdwtProd}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {SOURCE_LABELS[mailbox.accessSource] || mailbox.accessSource || "-"}
                  </TableCell>
                  <TableCell>
                    {mailbox.canManage ? (
                      <Badge variant="default">관리자</Badge>
                    ) : (
                      <Badge variant="outline">멤버</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-sm">{mailbox.memberCount ?? "-"}</TableCell>
                  <TableCell className="text-sm">{mailbox.myEmailCount ?? "-"}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {formatDate(mailbox.grantedAt || mailbox.myGrantedAt)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
