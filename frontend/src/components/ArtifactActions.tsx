import { getArtifactUrl } from '../api/resume'
import type { ArtifactKind } from '../types/resume'

interface ArtifactActionsProps {
  artifacts: Partial<Record<ArtifactKind, string | null>>
  cacheBust?: string
  jobId?: string
}

const downloadItems: Array<{ kind: ArtifactKind; label: string }> = [
  { kind: 'pdf', label: '下载 PDF' },
  { kind: 'tex', label: '下载 TEX' },
  { kind: 'json', label: '下载 JSON' },
]

export const ArtifactActions = ({ artifacts, cacheBust, jobId }: ArtifactActionsProps) => (
  <div className="action-group">
    {downloadItems.map((item) => {
      const enabled = Boolean(jobId && artifacts[item.kind])

      return (
        <a
          key={item.kind}
          className={`secondary-button ${enabled ? '' : 'is-disabled'}`}
          download
          href={enabled && jobId ? getArtifactUrl(jobId, item.kind, cacheBust) : undefined}
          onClick={(event) => {
            if (!enabled) {
              event.preventDefault()
            }
          }}
          rel="noreferrer"
          target={item.kind === 'pdf' ? '_blank' : undefined}
        >
          {item.label}
        </a>
      )
    })}
  </div>
)
