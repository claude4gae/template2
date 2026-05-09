import * as React from "react"
import {
  IconDeviceFloppy,
  IconPencil,
  IconPlus,
  IconTrash,
  IconX,
} from "@tabler/icons-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/common"
import { formatUpdatedAt } from "../../utils/lineSettings"

export function EarlyInformSettingsCard({
  lineId,
  formError,
  formValues,
  maxFieldLength,
  isCreating,
  entries,
  isLoading,
  hasLoadedOnce,
  editingId,
  editDraft,
  savingMap,
  rowErrors,
  onCreate,
  onFormChange,
  onEditChange,
  onSave,
  onCancelEditing,
  onStartEditing,
  onDelete,
}) {
  return (
    <div className="flex h-full min-h-0 flex-col rounded-lg border bg-background p-4 shadow-sm gap-4">
      <div className="flex flex-col gap-3">
        <div className="space-y-1">
          <h2 className="text-base font-medium">E-SOP Custom End Step 추가</h2>
          <p className="text-xs text-muted-foreground">
            line_id는 선택한 값으로 자동 저장되며 수정할 수 없습니다.
          </p>
        </div>

        {formError ? (
          <p className="text-xs text-destructive" role="alert">
            {formError}
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">&nbsp;</p>
        )}

        <form className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 lg:items-end" onSubmit={onCreate}>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground" htmlFor="main-step-input">
              Main Step
            </label>
            <Input
              id="main-step-input"
              value={formValues.mainStep}
              onChange={(event) => onFormChange("mainStep", event.target.value)}
              placeholder="ex) AB123456"
              required
              maxLength={maxFieldLength}
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground" htmlFor="custom-step-input">
              Early Inform Step
            </label>
            <Input
              id="custom-step-input"
              value={formValues.customEndStep}
              onChange={(event) => onFormChange("customEndStep", event.target.value)}
              placeholder="조기 알람 받을 스텝"
              maxLength={maxFieldLength}
            />
          </div>

          <div className="flex sm:justify-end lg:justify-start">
            <Button type="submit" disabled={isCreating || !lineId} className="w-full sm:w-auto">
              <IconPlus className="mr-1 size-4" />
              Add
            </Button>
          </div>
        </form>
      </div>

      <div className="min-h-0 min-w-0 flex-1 overflow-hidden rounded-lg border bg-background">
        <div className="h-full min-h-0 min-w-0 overflow-auto">
          <Table stickyHeader className="w-full table-fixed">
            <colgroup>
              <col className="w-30" />
              <col className="w-40" />
              <col className="w-40" />
              <col className="w-32" />
              <col className="w-40" />
              <col className="w-60" />
            </colgroup>

            <TableHeader className="sticky top-0 z-10 bg-muted">
              <TableRow>
                <TableHead className="text-center">Line ID</TableHead>
                <TableHead className="text-center">Main Step</TableHead>
                <TableHead className="text-center">Early Inform Step</TableHead>
                <TableHead className="text-center">Updated By</TableHead>
                <TableHead className="text-center">Updated At</TableHead>
                <TableHead className="text-right" />
              </TableRow>
            </TableHeader>

            <TableBody>
              {isLoading && !hasLoadedOnce && (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-sm text-muted-foreground">
                    Loading entries…
                  </TableCell>
                </TableRow>
              )}

              {!isLoading && entries.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-sm text-muted-foreground">
                    {lineId ? "No overrides found for this line." : "Select a line to view overrides."}
                  </TableCell>
                </TableRow>
              )}

              {entries.map((entry) => {
                const isEditing = editingId === entry.id
                const isSaving = Boolean(savingMap[entry.id])
                const rowError = rowErrors[entry.id]

                return (
                  <React.Fragment key={entry.id}>
                    <TableRow className={isSaving ? "opacity-60" : ""}>
                      <TableCell className="text-center font-light">{entry.lineId || "-"}</TableCell>

                      <TableCell className="text-center">
                        {isEditing ? (
                          <Input
                            value={editDraft.mainStep}
                            onChange={(event) => onEditChange("mainStep", event.target.value)}
                            maxLength={maxFieldLength}
                            disabled={isSaving}
                            className="text-center"
                          />
                        ) : (
                          <span className="font-light">{entry.mainStep}</span>
                        )}
                      </TableCell>

                      <TableCell className="text-center font-light">
                        {isEditing ? (
                          <Input
                            value={editDraft.customEndStep ?? ""}
                            onChange={(event) => onEditChange("customEndStep", event.target.value)}
                            maxLength={maxFieldLength}
                            disabled={isSaving}
                            className="text-center"
                          />
                        ) : entry.customEndStep && entry.customEndStep.trim().length > 0 ? (
                          entry.customEndStep
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>

                      <TableCell className="text-center text-xs text-muted-foreground">
                        {entry.updatedBy || "-"}
                      </TableCell>

                      <TableCell className="text-center text-xs text-muted-foreground">
                        {formatUpdatedAt(entry.updatedAt)}
                      </TableCell>

                      <TableCell className="text-end">
                        <div className="inline-flex items-center justify-end gap-2">
                          {isEditing ? (
                            <>
                              <Button size="sm" onClick={onSave} disabled={isSaving} className="gap-1">
                                <IconDeviceFloppy className="size-4" />
                                Save
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={onCancelEditing}
                                disabled={isSaving}
                                className="gap-1"
                              >
                                <IconX className="size-4" />
                                Cancel
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button size="sm" variant="ghost" onClick={() => onStartEditing(entry)} className="gap-1">
                                <IconPencil className="size-4" />
                                Edit
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => onDelete(entry)}
                                className="gap-1 text-destructive"
                              >
                                <IconTrash className="size-4" />
                                Delete
                              </Button>
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>

                    {rowError && (
                      <TableRow>
                        <TableCell colSpan={6} className="bg-destructive/5 px-4 py-2 text-center text-xs text-destructive">
                          {rowError}
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                )
              })}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}
