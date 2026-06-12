import { useQuery } from "@tanstack/react-query"

import { emailQueryKeys } from "../api/emailQueryKeys"
import { fetchEmailMailboxes, fetchEmailMailboxSummary } from "../api/emails"

export function useEmailMailboxes(options = {}) {
  return useQuery({
    queryKey: emailQueryKeys.mailboxes,
    queryFn: () => fetchEmailMailboxes(),
    staleTime: 5 * 60 * 1000,
    ...options,
  })
}

export function useEmailMailboxSummary() {
  return useQuery({
    queryKey: emailQueryKeys.mailboxSummary,
    queryFn: () => fetchEmailMailboxSummary(),
    staleTime: 5 * 60 * 1000,
  })
}
