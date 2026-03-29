import { SECTION_LABELS } from '../constants/resume'
import type { ResumeSection } from '../types/resume'

interface SectionRegenerateActionsProps {
  activeSection: ResumeSection | null
  availableSections: ResumeSection[]
  onRegenerate: (section: ResumeSection) => void
}

export const SectionRegenerateActions = ({
  activeSection,
  availableSections,
  onRegenerate,
}: SectionRegenerateActionsProps) => (
  <div className="section-actions">
    {availableSections.map((section) => (
      <button
        key={section}
        className="ghost-button"
        disabled={Boolean(activeSection)}
        onClick={() => onRegenerate(section)}
        type="button"
      >
        {activeSection === section
          ? `正在重生成 ${SECTION_LABELS[section]}...`
          : `快速重生成 ${SECTION_LABELS[section]}`}
      </button>
    ))}
  </div>
)
