import { BasicInfoPanel } from './BasicInfoPanel'
import { ThemePicker } from './ThemePicker'
import type { ResumeFormValues } from '../types/resume'

interface ResumeFormProps {
  errors: Record<string, string>
  isSubmitting: boolean
  values: ResumeFormValues
  onChange: (field: keyof ResumeFormValues, value: string) => void
  onBasicInfoChange: (field: keyof ResumeFormValues['basicInfo'], value: string) => void
  onThemeChange: (themeId: ResumeFormValues['themeId']) => void
  onSubmit: () => void
}

export const ResumeForm = ({
  errors,
  isSubmitting,
  values,
  onChange,
  onBasicInfoChange,
  onThemeChange,
  onSubmit,
}: ResumeFormProps) => (
  <section className="panel input-panel">
    <div className="panel-header">
      <div>
        <span className="panel-tag">输入区</span>
        <h2>提交岗位与个人经历</h2>
      </div>
      <p>推荐直接粘贴完整经历原文，保留项目、实习、教育和技能细节，再选择一套更适合你的简历主题。</p>
    </div>

    <div className="form-layout">
      <ThemePicker selectedThemeId={values.themeId} onSelect={onThemeChange} />

      <label className="field">
        <span>目标岗位</span>
        <input
          value={values.targetRole}
          onChange={(event) => onChange('targetRole', event.target.value)}
          placeholder="例如：数据分析师 / 算法工程师 / 产品经理"
        />
        {errors.targetRole ? <small className="field-error">{errors.targetRole}</small> : null}
      </label>

      <label className="field">
        <span>岗位描述</span>
        <textarea
          value={values.jobDescription}
          onChange={(event) => onChange('jobDescription', event.target.value)}
          placeholder="粘贴 JD，包含职责、技能要求、关键词和加分项。"
          rows={8}
        />
        {errors.jobDescription ? <small className="field-error">{errors.jobDescription}</small> : null}
      </label>

      <label className="field">
        <span>个人经历原文</span>
        <textarea
          value={values.rawExperienceText}
          onChange={(event) => onChange('rawExperienceText', event.target.value)}
          placeholder="粘贴你的项目、实习、教育、技能、竞赛等原始材料，越完整越好。"
          rows={12}
        />
        {errors.rawExperienceText ? (
          <small className="field-error">{errors.rawExperienceText}</small>
        ) : null}
      </label>

      <BasicInfoPanel values={values.basicInfo} onChange={onBasicInfoChange} />

      <button className="primary-button" disabled={isSubmitting} onClick={onSubmit} type="button">
        {isSubmitting ? '正在创建任务...' : '开始生成简历'}
      </button>
    </div>
  </section>
)
