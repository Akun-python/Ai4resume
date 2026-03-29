import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'

const createJsonResponse = (payload: unknown, status = 200) =>
  new Response(JSON.stringify(payload), {
    status,
    headers: {
      'Content-Type': 'application/json',
    },
  })

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it('blocks submission when required fields are empty', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: '开始生成简历' }))

    expect(screen.getByText('请输入目标岗位类型。')).toBeInTheDocument()
    expect(screen.getByText('请输入岗位描述。')).toBeInTheDocument()
    expect(screen.getByText('请输入个人经历原文。')).toBeInTheDocument()
    expect(fetch).not.toHaveBeenCalled()
  })

  it(
    'creates a themed job, polls to success, opens refine drawer, and submits section refine',
    async () => {
      const user = userEvent.setup()
      const fetchMock = vi.mocked(fetch)

      fetchMock
        .mockResolvedValueOnce(createJsonResponse({ job_id: 'job-001', status: 'pending' }, 202))
        .mockResolvedValueOnce(
          createJsonResponse({
            job_id: 'job-001',
            status: 'succeeded',
            available_sections: ['summary', 'projects', 'experience'],
            artifacts: {
              pdf: '/tmp/resume.pdf',
              tex: '/tmp/resume.tex',
              json: '/tmp/resume.json',
            },
            parsed_profile_summary: {
              education_count: 1,
              experience_count: 1,
              project_count: 1,
              skill_group_count: 1,
            },
            presentation: { theme_id: 'forest_slate' },
            preview_sections: [
              { section: 'summary', title: '职业概述', order: 0 },
              { section: 'projects', title: '项目经历', order: 1 },
            ],
            updated_at: '2026-03-29T10:00:00Z',
          }),
        )
        .mockResolvedValueOnce(createJsonResponse({ job_id: 'job-002', status: 'pending' }, 202))
        .mockResolvedValueOnce(
          createJsonResponse({
            job_id: 'job-002',
            parent_job_id: 'job-001',
            section_to_regenerate: 'projects',
            status: 'succeeded',
            available_sections: ['summary', 'projects', 'experience'],
            artifacts: {
              pdf: '/tmp/resume-v2.pdf',
              tex: '/tmp/resume-v2.tex',
              json: '/tmp/resume-v2.json',
            },
            parsed_profile_summary: {
              education_count: 1,
              experience_count: 1,
              project_count: 1,
              skill_group_count: 1,
            },
            presentation: { theme_id: 'terracotta_ink' },
            preview_sections: [
              { section: 'summary', title: '职业概述', order: 0 },
              { section: 'projects', title: '项目经历', order: 1 },
            ],
            updated_at: '2026-03-29T10:01:00Z',
          }),
        )

      render(<App />)

      await user.click(screen.getAllByRole('button', { name: /Forest Slate/ })[0])
      await user.type(screen.getByLabelText('目标岗位'), '数据分析师')
      await user.type(screen.getByLabelText('岗位描述'), '需要 SQL、Python、指标体系和增长分析能力。')
      await user.type(screen.getByLabelText('个人经历原文'), '负责自动化报表、增长分析与复盘汇报。')
      await user.click(screen.getByRole('button', { name: '开始生成简历' }))

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          '/v1/resume/jobs',
          expect.objectContaining({ method: 'POST' }),
        )
      })

      const createRequest = fetchMock.mock.calls[0]?.[1]
      expect(createRequest).toBeDefined()
      expect(JSON.parse(String((createRequest as RequestInit).body))).toMatchObject({
        presentation_options: { theme_id: 'forest_slate' },
      })

      await waitFor(() => {
        expect(screen.getByText('简历生成完成')).toBeInTheDocument()
      })

      expect(screen.getByLabelText('PDF 预览')).toBeInTheDocument()
      expect(screen.getByRole('link', { name: '下载 PDF' })).toHaveAttribute(
        'href',
        '/v1/resume/jobs/job-001/artifacts/pdf?t=2026-03-29T10%3A00%3A00Z',
      )

      await user.click(screen.getByText('编辑与润色'))
      await user.click(screen.getByRole('button', { name: /点击优化 项目经历/ }))

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: '优化 项目经历' })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /更突出成果/ }))
      await user.type(screen.getByLabelText('补充要求'), '更强调可交付成果和汇报表达。')
      await user.click(screen.getAllByRole('button', { name: /Terracotta Ink/ })[1])
      await user.click(screen.getByRole('button', { name: '提交区块润色' }))

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          '/v1/resume/jobs/job-001/sections/projects/regenerate',
          expect.objectContaining({ method: 'POST' }),
        )
      })

      const regenerateRequest = fetchMock.mock.calls[2]?.[1]
      expect(regenerateRequest).toBeDefined()
      expect(JSON.parse(String((regenerateRequest as RequestInit).body))).toMatchObject({
        preset: 'more_results_focused',
        custom_instruction: '更强调可交付成果和汇报表达。',
        theme_id: 'terracotta_ink',
      })

      await user.click(screen.getByText('展开任务详情'))
      await waitFor(() => {
        expect(screen.getByText('job-001')).toBeInTheDocument()
      })

      await waitFor(() => {
        expect(screen.getByRole('link', { name: '下载 PDF' })).toHaveAttribute(
          'href',
          '/v1/resume/jobs/job-002/artifacts/pdf?t=2026-03-29T10%3A01%3A00Z',
        )
      })
    },
    15000,
  )

  it('shows failure messages and keeps the user input intact', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.mocked(fetch)

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ job_id: 'job-003', status: 'pending' }, 202))
      .mockResolvedValueOnce(
        createJsonResponse({
          job_id: 'job-003',
          status: 'failed',
          error_message: 'LaTeX compilation failed',
          available_sections: [],
          artifacts: {},
          parsed_profile_summary: {
            education_count: 0,
            experience_count: 0,
            project_count: 0,
            skill_group_count: 0,
          },
          presentation: { theme_id: 'executive_blue' },
          preview_sections: [],
          updated_at: '2026-03-29T10:02:00Z',
        }),
      )

    render(<App />)

    await user.type(screen.getByLabelText('目标岗位'), '算法工程师')
    await user.type(screen.getByLabelText('岗位描述'), '需要机器学习和 Python 能力。')
    await user.type(screen.getByLabelText('个人经历原文'), '做过推荐系统和特征工程。')
    await user.click(screen.getByRole('button', { name: '开始生成简历' }))

    await waitFor(() => {
      expect(screen.getByText('生成失败')).toBeInTheDocument()
    })

    expect(screen.getByText('LaTeX compilation failed')).toBeInTheDocument()
    expect(screen.getByDisplayValue('算法工程师')).toBeInTheDocument()
    expect(screen.getByDisplayValue('需要机器学习和 Python 能力。')).toBeInTheDocument()
    expect(screen.getByDisplayValue('做过推荐系统和特征工程。')).toBeInTheDocument()
  })
})
