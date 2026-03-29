import {
  REFINE_PRESET_DESCRIPTIONS,
  REFINE_PRESET_LABELS,
  SECTION_LABELS,
} from '../constants/resume'
import { ThemePicker } from './ThemePicker'
import type { RefineFormValues, ResumeSection } from '../types/resume'

interface RefineDrawerProps {
  activeSection: ResumeSection | null
  isSubmitting: boolean
  values: RefineFormValues
  onChange: (values: RefineFormValues) => void
  onClose: () => void
  onSubmit: () => void
}

export const RefineDrawer = ({
  activeSection,
  isSubmitting,
  values,
  onChange,
  onClose,
  onSubmit,
}: RefineDrawerProps) => (
  <aside className={`refine-drawer ${activeSection ? 'refine-drawer-open' : ''}`}>
    <div className="refine-drawer-card">
      <div className="refine-drawer-header">
        <div>
          <span className="panel-tag">AI 润色</span>
          <h3>{activeSection ? `优化 ${SECTION_LABELS[activeSection]}` : '选择区块后开始润色'}</h3>
        </div>
        <button className="ghost-button refine-close" onClick={onClose} type="button">
          关闭
        </button>
      </div>

      <div className="refine-content">
        <div className="refine-presets">
          {Object.entries(REFINE_PRESET_LABELS).map(([preset, label]) => (
            <button
              key={preset}
              className={`preset-chip ${values.preset === preset ? 'preset-chip-active' : ''}`}
              onClick={() =>
                onChange({
                  ...values,
                  preset: preset as RefineFormValues['preset'],
                })
              }
              type="button"
            >
              <strong>{label}</strong>
              <small>{REFINE_PRESET_DESCRIPTIONS[preset as keyof typeof REFINE_PRESET_DESCRIPTIONS]}</small>
            </button>
          ))}
        </div>

        <label className="field">
          <span>补充要求</span>
          <textarea
            value={values.customInstruction}
            onChange={(event) =>
              onChange({
                ...values,
                customInstruction: event.target.value,
              })
            }
            placeholder="例如：更强调业务影响、减少重复表达、突出协作推进和汇报能力。"
            rows={5}
          />
        </label>

        <ThemePicker
          selectedThemeId={values.themeId}
          title="同步切换主题"
          onSelect={(themeId) =>
            onChange({
              ...values,
              themeId,
            })
          }
        />

        <button className="primary-button" disabled={!activeSection || isSubmitting} onClick={onSubmit} type="button">
          {isSubmitting ? '正在提交润色...' : '提交区块润色'}
        </button>
      </div>
    </div>
  </aside>
)
