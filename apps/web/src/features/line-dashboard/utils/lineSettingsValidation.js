import { MAX_FIELD_LENGTH } from "./lineSettingsConfig"
import { normalizeDraft } from "./lineSettings"

export function validateStepDraft({ mainStep, customEndStep }) {
  const normalizedMainStep = normalizeDraft(mainStep)
  const normalizedCustom = normalizeDraft(customEndStep ?? "")

  if (!normalizedMainStep) {
    return { error: "Main step is required" }
  }
  if (normalizedMainStep.length > MAX_FIELD_LENGTH) {
    return { error: `Main step must be ${MAX_FIELD_LENGTH} characters or fewer` }
  }
  if (normalizedCustom.length > MAX_FIELD_LENGTH) {
    return { error: `Custom end step must be ${MAX_FIELD_LENGTH} characters or fewer` }
  }

  return {
    normalizedMainStep,
    normalizedCustom,
    error: null,
  }
}
