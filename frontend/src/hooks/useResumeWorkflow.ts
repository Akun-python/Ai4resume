import { startTransition, useEffect, useEffectEvent, useRef, useState } from 'react'

import { createResumeJob, fetchJobStatus, getArtifactUrl, regenerateSection } from '../api/resume'
import {
  DEFAULT_THEME_ID,
  INITIAL_FORM_VALUES,
  INITIAL_REFINE_VALUES,
  POLL_INTERVAL_MS,
} from '../constants/resume'
import type {
  JobStatusResponse,
  RefineFormValues,
  ResumeFormValues,
  ResumeSection,
} from '../types/resume'
import {
  hasValidationErrors,
  toRefinePayload,
  toRequestPayload,
  validateForm,
} from '../utils/forms'

export const useResumeWorkflow = () => {
  const pollInterval =
    import.meta.env.MODE === 'test'
      ? 1
      : Number(import.meta.env.VITE_POLL_INTERVAL_MS ?? POLL_INTERVAL_MS)

  const [formValues, setFormValues] = useState<ResumeFormValues>(INITIAL_FORM_VALUES)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [currentJob, setCurrentJob] = useState<JobStatusResponse | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [pageError, setPageError] = useState('')
  const [isRegeneratingSection, setIsRegeneratingSection] = useState<ResumeSection | null>(null)
  const [activeRefineSection, setActiveRefineSection] = useState<ResumeSection | null>(null)
  const [refineValues, setRefineValues] = useState<RefineFormValues>(INITIAL_REFINE_VALUES)
  const pollingTimerRef = useRef<number | null>(null)

  const clearPolling = () => {
    if (pollingTimerRef.current !== null) {
      window.clearTimeout(pollingTimerRef.current)
      pollingTimerRef.current = null
    }
  }

  const stopPolling = () => {
    clearPolling()
    setIsPolling(false)
  }

  const schedulePoll = (jobId: string) => {
    clearPolling()
    pollingTimerRef.current = window.setTimeout(() => {
      void pollJob(jobId)
    }, pollInterval)
  }

  const pollJob = useEffectEvent(async (jobId: string) => {
    try {
      const nextJob = await fetchJobStatus(jobId)
      startTransition(() => {
        setCurrentJob(nextJob)
      })

      if (
        nextJob.status === 'pending' ||
        nextJob.status === 'parsing' ||
        nextJob.status === 'drafting' ||
        nextJob.status === 'rendering' ||
        nextJob.status === 'compiling'
      ) {
        setIsPolling(true)
        schedulePoll(jobId)
      } else {
        stopPolling()
      }
    } catch (error) {
      stopPolling()
      setPageError(error instanceof Error ? error.message : '查询任务状态失败。')
    }
  })

  useEffect(() => {
    return () => {
      clearPolling()
    }
  }, [])

  const submit = async () => {
    const nextErrors = validateForm(formValues)
    setFieldErrors(nextErrors)

    if (hasValidationErrors(nextErrors)) {
      return
    }

    setPageError('')
    setIsSubmitting(true)

    try {
      const response = await createResumeJob(toRequestPayload(formValues))
      const pendingJob: JobStatusResponse = {
        job_id: response.job_id,
        status: response.status,
        available_sections: [],
        artifacts: {},
        parsed_profile_summary: {
          education_count: 0,
          experience_count: 0,
          project_count: 0,
          skill_group_count: 0,
        },
        presentation: { theme_id: formValues.themeId },
        preview_sections: [],
        updated_at: new Date().toISOString(),
      }

      setCurrentJob(pendingJob)
      setIsPolling(true)
      void pollJob(response.job_id)
    } catch (error) {
      setPageError(error instanceof Error ? error.message : '任务创建失败。')
    } finally {
      setIsSubmitting(false)
    }
  }

  const submitRegeneration = async (section: ResumeSection, values?: RefineFormValues) => {
    if (!currentJob?.job_id) {
      return
    }

    const nextValues = values ?? refineValues
    setPageError('')
    setIsRegeneratingSection(section)

    try {
      const response = await regenerateSection(
        currentJob.job_id,
        section,
        values ? toRefinePayload(nextValues) : undefined,
      )
      const nextTheme = values ? nextValues.themeId : currentJob.presentation.theme_id
      const childJob: JobStatusResponse = {
        job_id: response.job_id,
        parent_job_id: currentJob.job_id,
        section_to_regenerate: section,
        status: response.status,
        available_sections: currentJob.available_sections,
        artifacts: {},
        parsed_profile_summary: currentJob.parsed_profile_summary,
        presentation: { theme_id: nextTheme },
        preview_sections: currentJob.preview_sections,
        updated_at: new Date().toISOString(),
      }

      setCurrentJob(childJob)
      setIsPolling(true)
      void pollJob(response.job_id)
      if (values) {
        setActiveRefineSection(null)
      }
    } catch (error) {
      setPageError(error instanceof Error ? error.message : '区块润色失败。')
    } finally {
      setIsRegeneratingSection(null)
    }
  }

  const openRefinePanel = (section: ResumeSection) => {
    const themeId = currentJob?.presentation.theme_id ?? formValues.themeId ?? DEFAULT_THEME_ID
    setRefineValues({
      ...INITIAL_REFINE_VALUES,
      themeId,
    })
    setActiveRefineSection(section)
  }

  const closeRefinePanel = () => {
    setActiveRefineSection(null)
  }

  const pdfPreviewUrl =
    currentJob?.job_id && currentJob.artifacts.pdf
      ? getArtifactUrl(currentJob.job_id, 'pdf', currentJob.updated_at)
      : ''

  const activeThemeId = currentJob?.presentation.theme_id ?? formValues.themeId

  return {
    activeRefineSection,
    activeThemeId,
    closeRefinePanel,
    currentJob,
    fieldErrors,
    formValues,
    isPolling,
    isRegeneratingSection,
    isSubmitting,
    pageError,
    pdfPreviewUrl,
    refineValues,
    setFieldErrors,
    setFormValues,
    setRefineValues,
    openRefinePanel,
    submit,
    submitRegeneration,
  }
}
