import { SECTION_LABELS, STATUS_LABELS, THEME_OPTIONS } from '../constants/resume'
import type { JobStatusResponse } from '../types/resume'
import { formatTimestamp, shortenJobId } from '../utils/format'

interface JobStatusCardProps {
  isPolling: boolean
  job: JobStatusResponse | null
  pageError: string
}

export const JobStatusCard = ({ isPolling, job, pageError }: JobStatusCardProps) => (
  <section className="panel status-panel">
    <div className="panel-header">
      <div>
        <span className="panel-tag">任务区</span>
        <h2>生成状态</h2>
      </div>
      <p>状态信息默认精简展示，详细任务信息按需展开。</p>
    </div>

    {pageError ? <div className="alert alert-error">{pageError}</div> : null}

    {!job ? (
      <div className="empty-state">
        <strong>还没有任务</strong>
        <span>提交左侧表单后，这里会显示 job id、状态进度、主题和结构摘要。</span>
      </div>
    ) : (
      <div className="status-card">
        <div className="status-topline">
          <span className={`status-pill status-${job.status}`}>{STATUS_LABELS[job.status]}</span>
          {isPolling ? <span className="live-indicator">轮询中</span> : null}
        </div>

        <div className="status-inline">
          <span title={job.job_id}>任务 {shortenJobId(job.job_id)}</span>
          <span>{job.section_to_regenerate ? SECTION_LABELS[job.section_to_regenerate] : '整份生成'}</span>
          <span>{THEME_OPTIONS.find((item) => item.id === job.presentation.theme_id)?.name ?? job.presentation.theme_id}</span>
        </div>

        <details className="status-details">
          <summary>展开任务详情</summary>
          <dl className="meta-grid">
            <div>
              <dt>当前任务</dt>
              <dd title={job.job_id}>{shortenJobId(job.job_id)}</dd>
            </div>
            <div>
              <dt>父任务</dt>
              <dd title={job.parent_job_id ?? ''}>{job.parent_job_id ? shortenJobId(job.parent_job_id) : '无'}</dd>
            </div>
            <div>
              <dt>当前优化区块</dt>
              <dd>{job.section_to_regenerate ? SECTION_LABELS[job.section_to_regenerate] : '整份生成'}</dd>
            </div>
            <div>
              <dt>主题</dt>
              <dd>{THEME_OPTIONS.find((item) => item.id === job.presentation.theme_id)?.name ?? job.presentation.theme_id}</dd>
            </div>
            <div>
              <dt>更新时间</dt>
              <dd>{formatTimestamp(job.updated_at)}</dd>
            </div>
          </dl>

          <div className="summary-strip">
            <span>教育 {job.parsed_profile_summary.education_count}</span>
            <span>经历 {job.parsed_profile_summary.experience_count}</span>
            <span>项目 {job.parsed_profile_summary.project_count}</span>
            <span>技能组 {job.parsed_profile_summary.skill_group_count}</span>
          </div>
        </details>

        {job.error_message ? <div className="alert alert-error">{job.error_message}</div> : null}
      </div>
    )}
  </section>
)
