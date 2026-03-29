import type {
  ArtifactKind,
  JobCreateResponse,
  JobStatusResponse,
  ResumeGenerationRequest,
  ResumeSection,
  SectionRefineRequest,
} from '../types/resume'

const API_ROOT = '/v1/resume/jobs'

const parseJson = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    let message = `请求失败：${response.status}`
    const rawText = await response.text()

    try {
      const data = JSON.parse(rawText) as { detail?: string; message?: string }
      if (data.detail) {
        message = data.detail
      } else if (data.message) {
        message = data.message
      }
    } catch {
      if (rawText.trim()) {
        message = rawText
      }
    }

    throw new Error(message)
  }

  return (await response.json()) as T
}

export const createResumeJob = async (payload: ResumeGenerationRequest) => {
  const response = await fetch(API_ROOT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  return parseJson<JobCreateResponse>(response)
}

export const fetchJobStatus = async (jobId: string) => {
  const response = await fetch(`${API_ROOT}/${jobId}`)
  return parseJson<JobStatusResponse>(response)
}

export const regenerateSection = async (
  jobId: string,
  section: ResumeSection,
  payload?: SectionRefineRequest,
) => {
  const response = await fetch(`${API_ROOT}/${jobId}/sections/${section}/regenerate`, {
    method: 'POST',
    headers: payload
      ? {
          'Content-Type': 'application/json',
        }
      : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  })

  return parseJson<JobCreateResponse>(response)
}

export const getArtifactUrl = (jobId: string, kind: ArtifactKind, cacheBust?: string) => {
  const baseUrl = `${API_ROOT}/${jobId}/artifacts/${kind}`
  return cacheBust ? `${baseUrl}?t=${encodeURIComponent(cacheBust)}` : baseUrl
}
