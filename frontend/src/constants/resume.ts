import type {
  JobStatus,
  RefineFormValues,
  RefinePreset,
  ResumeFormValues,
  ResumeSection,
  ThemeId,
  ThemeOption,
} from '../types/resume'

export const DEFAULT_THEME_ID: ThemeId = 'executive_blue'

export const INITIAL_FORM_VALUES: ResumeFormValues = {
  targetRole: '',
  jobDescription: '',
  rawExperienceText: '',
  themeId: DEFAULT_THEME_ID,
  basicInfo: {
    name: '',
    phone: '',
    email: '',
    city: '',
    linksText: '',
  },
}

export const INITIAL_REFINE_VALUES: RefineFormValues = {
  preset: 'more_role_aligned',
  customInstruction: '',
  themeId: DEFAULT_THEME_ID,
}

export const STATUS_LABELS: Record<JobStatus, string> = {
  pending: '任务已创建，等待执行',
  parsing: '正在解析个人经历',
  drafting: '正在生成简历内容',
  rendering: '正在渲染 LaTeX 模板',
  compiling: '正在编译 PDF',
  succeeded: '简历生成完成',
  failed: '生成失败',
}

export const SECTION_LABELS: Record<ResumeSection, string> = {
  summary: '职业概述',
  skills: '核心技能',
  projects: '项目经历',
  experience: '工作经历',
  education: '教育经历',
}

export const REFINE_PRESET_LABELS: Record<RefinePreset, string> = {
  more_professional: '更专业',
  more_concise: '更简洁',
  more_results_focused: '更突出成果',
  more_role_aligned: '更匹配岗位',
  more_executive: '更成熟克制',
}

export const REFINE_PRESET_DESCRIPTIONS: Record<RefinePreset, string> = {
  more_professional: '适合正式求职投递，减少口语感。',
  more_concise: '压缩篇幅，保留高信息密度。',
  more_results_focused: '强调成果、产出和可交付物。',
  more_role_aligned: '更贴近岗位关键词和能力要求。',
  more_executive: '突出判断、推进与协作表达。',
}

export const THEME_OPTIONS: ThemeOption[] = [
  {
    id: 'executive_blue',
    name: 'Executive Blue',
    description: '冷静商务蓝，适合数据、咨询、运营类岗位。',
    swatches: ['#1d5c8f', '#eaf2f8', '#1e2a37'],
  },
  {
    id: 'forest_slate',
    name: 'Forest Slate',
    description: '深绿灰，偏稳重顾问风。',
    swatches: ['#335c53', '#ebf3f0', '#1f2c2a'],
  },
  {
    id: 'terracotta_ink',
    name: 'Terracotta Ink',
    description: '暖陶土棕，偏产品与品牌高级感。',
    swatches: ['#9c5e44', '#faefe8', '#322823'],
  },
]

export const POLL_INTERVAL_MS = 2500
