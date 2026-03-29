export type ResumeSection =
  | 'summary'
  | 'skills'
  | 'projects'
  | 'experience'
  | 'education'

export type JobStatus =
  | 'pending'
  | 'parsing'
  | 'drafting'
  | 'rendering'
  | 'compiling'
  | 'succeeded'
  | 'failed'

export type ArtifactKind = 'json' | 'tex' | 'pdf'
export type ThemeId = 'executive_blue' | 'forest_slate' | 'terracotta_ink'
export type RefinePreset =
  | 'more_professional'
  | 'more_concise'
  | 'more_results_focused'
  | 'more_role_aligned'
  | 'more_executive'

export interface BasicInfoPayload {
  name?: string
  phone?: string
  email?: string
  city?: string
  links?: string[]
}

export interface PresentationOptions {
  theme_id: ThemeId
}

export interface ResumeGenerationRequest {
  raw_experience_text: string
  job_description: string
  target_role: string
  basic_info?: BasicInfoPayload
  presentation_options: PresentationOptions
}

export interface SectionRefineRequest {
  preset?: RefinePreset | null
  custom_instruction?: string | null
  theme_id?: ThemeId | null
}

export interface JobCreateResponse {
  job_id: string
  status: JobStatus
}

export interface PreviewSection {
  section: ResumeSection
  title: string
  order: number
}

export interface JobStatusResponse {
  job_id: string
  parent_job_id?: string | null
  section_to_regenerate?: ResumeSection | null
  status: JobStatus
  error_message?: string | null
  available_sections: ResumeSection[]
  artifacts: Partial<Record<ArtifactKind, string | null>>
  parsed_profile_summary: {
    education_count: number
    experience_count: number
    project_count: number
    skill_group_count: number
  }
  presentation: PresentationOptions
  preview_sections: PreviewSection[]
  updated_at: string
}

export interface ThemeOption {
  id: ThemeId
  name: string
  description: string
  swatches: [string, string, string]
}

export interface ResumeFormValues {
  targetRole: string
  jobDescription: string
  rawExperienceText: string
  themeId: ThemeId
  basicInfo: {
    name: string
    phone: string
    email: string
    city: string
    linksText: string
  }
}

export interface RefineFormValues {
  preset: RefinePreset
  customInstruction: string
  themeId: ThemeId
}
