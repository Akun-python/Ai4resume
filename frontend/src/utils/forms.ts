import type {
  BasicInfoPayload,
  RefineFormValues,
  ResumeFormValues,
  ResumeGenerationRequest,
  SectionRefineRequest,
} from '../types/resume'

const trimOrUndefined = (value: string) => {
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : undefined
}

export const toLinksArray = (linksText: string) =>
  linksText
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean)

export const toRequestPayload = (values: ResumeFormValues): ResumeGenerationRequest => {
  const basicInfo: BasicInfoPayload = {
    name: trimOrUndefined(values.basicInfo.name),
    phone: trimOrUndefined(values.basicInfo.phone),
    email: trimOrUndefined(values.basicInfo.email),
    city: trimOrUndefined(values.basicInfo.city),
    links: toLinksArray(values.basicInfo.linksText),
  }

  const hasBasicInfo = Object.values(basicInfo).some((value) =>
    Array.isArray(value) ? value.length > 0 : Boolean(value),
  )

  return {
    target_role: values.targetRole.trim(),
    job_description: values.jobDescription.trim(),
    raw_experience_text: values.rawExperienceText.trim(),
    basic_info: hasBasicInfo ? basicInfo : undefined,
    presentation_options: {
      theme_id: values.themeId,
    },
  }
}

export const toRefinePayload = (values: RefineFormValues): SectionRefineRequest => ({
  preset: values.preset,
  custom_instruction: trimOrUndefined(values.customInstruction) ?? null,
  theme_id: values.themeId,
})

export const validateForm = (values: ResumeFormValues) => ({
  targetRole: values.targetRole.trim().length === 0 ? '请输入目标岗位类型。' : '',
  jobDescription: values.jobDescription.trim().length === 0 ? '请输入岗位描述。' : '',
  rawExperienceText: values.rawExperienceText.trim().length === 0 ? '请输入个人经历原文。' : '',
})

export const hasValidationErrors = (errors: Record<string, string>) =>
  Object.values(errors).some(Boolean)
