import { getArtifactUrl } from '../api/resume'
import { ArtifactActions } from './ArtifactActions'
import { SectionRegenerateActions } from './SectionRegenerateActions'
import { SECTION_LABELS } from '../constants/resume'
import type { JobStatusResponse, ResumeSection } from '../types/resume'

interface PdfPreviewPanelProps {
  isRegeneratingSection: ResumeSection | null
  job: JobStatusResponse | null
  pdfPreviewUrl: string
  onOpenRefine: (section: ResumeSection) => void
  onQuickRegenerate: (section: ResumeSection) => void
}

export const PdfPreviewPanel = ({
  isRegeneratingSection,
  job,
  pdfPreviewUrl,
  onOpenRefine,
  onQuickRegenerate,
}: PdfPreviewPanelProps) => (
  <section className="panel preview-panel">
    <div className="panel-header">
      <div>
        <span className="panel-tag">结果区</span>
        <h2>PDF 预览与 AI 润色</h2>
      </div>
      <p>预览是主舞台，下载、区块编辑和快速重生成都收进按需展开的工具层。</p>
    </div>

    {!job || job.status !== 'succeeded' ? (
      <div className="empty-state empty-preview">
        <strong>结果尚未就绪</strong>
        <span>任务成功后，这里会显示 PDF 预览、区块热点层和单模块润色入口。</span>
      </div>
    ) : (
      <>
        <div className="preview-toolbar">
          <ArtifactActions artifacts={job.artifacts} cacheBust={job.updated_at} jobId={job.job_id} />
          {job.artifacts.pdf ? (
            <a
              className="text-link"
              href={getArtifactUrl(job.job_id, 'pdf', job.updated_at)}
              rel="noreferrer"
              target="_blank"
            >
              新窗口打开 PDF
            </a>
          ) : null}
        </div>

        <div className="preview-layout preview-layout-single">
          <div className="pdf-preview-frame">
            {job.artifacts.pdf ? (
              <iframe
                aria-label="PDF 预览"
                className="pdf-object"
                src={pdfPreviewUrl}
                title="PDF 预览"
              />
            ) : (
              <div className="empty-state">
                <strong>暂时没有 PDF 文件</strong>
                <span>你仍可尝试下载其他产物，或重新提交任务。</span>
              </div>
            )}
          </div>
        </div>

        <details className="preview-tools">
          <summary>
            <span>编辑与润色</span>
            <small>按需展开区块操作</small>
          </summary>

          <div className="preview-tools-body">
            <div className="preview-hotspots">
              <div className="preview-hotspots-header">
                <strong>点击模块开始 AI 润色</strong>
                <span>首版以区块级热点代替精确坐标点击。</span>
              </div>
              <div className="preview-hotspots-list">
                {job.preview_sections.map((item) => (
                  <button
                    key={item.section}
                    className="hotspot-card"
                    disabled={Boolean(isRegeneratingSection)}
                    onClick={() => onOpenRefine(item.section)}
                    type="button"
                  >
                    <span className="hotspot-index">{item.order + 1}</span>
                    <div>
                      <strong>{item.title}</strong>
                      <small>点击优化 {SECTION_LABELS[item.section]}</small>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="regenerate-box regenerate-box-embedded">
              <h3>快速重生成</h3>
              <p>如果只想快速刷新某个模块，可直接触发无指令重生成。</p>
              <SectionRegenerateActions
                activeSection={isRegeneratingSection}
                availableSections={job.available_sections}
                onRegenerate={onQuickRegenerate}
              />
            </div>
          </div>
        </details>
      </>
    )}
  </section>
)
