import type { ResumeFormValues } from '../types/resume'

interface BasicInfoPanelProps {
  values: ResumeFormValues['basicInfo']
  onChange: (field: keyof ResumeFormValues['basicInfo'], value: string) => void
}

export const BasicInfoPanel = ({ values, onChange }: BasicInfoPanelProps) => (
  <details className="basic-info-panel">
    <summary>基础信息（可选）</summary>
    <div className="basic-info-grid">
      <label className="field">
        <span>姓名</span>
        <input
          value={values.name}
          onChange={(event) => onChange('name', event.target.value)}
          placeholder="例如：张三"
        />
      </label>

      <label className="field">
        <span>电话</span>
        <input
          value={values.phone}
          onChange={(event) => onChange('phone', event.target.value)}
          placeholder="例如：13800000000"
        />
      </label>

      <label className="field">
        <span>邮箱</span>
        <input
          value={values.email}
          onChange={(event) => onChange('email', event.target.value)}
          placeholder="例如：hello@example.com"
        />
      </label>

      <label className="field">
        <span>城市</span>
        <input
          value={values.city}
          onChange={(event) => onChange('city', event.target.value)}
          placeholder="例如：上海"
        />
      </label>

      <label className="field field-full">
        <span>链接</span>
        <textarea
          value={values.linksText}
          onChange={(event) => onChange('linksText', event.target.value)}
          rows={4}
          placeholder={'每行一个链接，例如：\nhttps://github.com/yourname\nhttps://www.linkedin.com/in/yourname'}
        />
      </label>
    </div>
  </details>
)
