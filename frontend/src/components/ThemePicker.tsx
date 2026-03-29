import { THEME_OPTIONS } from '../constants/resume'
import type { ThemeId } from '../types/resume'

interface ThemePickerProps {
  selectedThemeId: ThemeId
  title?: string
  onSelect: (themeId: ThemeId) => void
}

export const ThemePicker = ({ selectedThemeId, title = '主题风格', onSelect }: ThemePickerProps) => (
  <div className="theme-picker">
    <div className="theme-picker-header">
      <span>{title}</span>
      <small>保持 ATS 稳健结构，仅切换视觉语气。</small>
    </div>
    <div className="theme-grid">
      {THEME_OPTIONS.map((theme) => (
        <button
          key={theme.id}
          className={`theme-card ${selectedThemeId === theme.id ? 'theme-card-active' : ''}`}
          onClick={() => onSelect(theme.id)}
          type="button"
        >
          <div className="theme-swatches" aria-hidden="true">
            {theme.swatches.map((swatch) => (
              <span key={swatch} style={{ backgroundColor: swatch }} />
            ))}
          </div>
          <strong>{theme.name}</strong>
          <small>{theme.description}</small>
        </button>
      ))}
    </div>
  </div>
)
