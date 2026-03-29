import './App.css'

import { AppShell } from './components/AppShell'
import { HeroPanel } from './components/HeroPanel'
import { JobStatusCard } from './components/JobStatusCard'
import { PdfPreviewPanel } from './components/PdfPreviewPanel'
import { RefineDrawer } from './components/RefineDrawer'
import { ResumeForm } from './components/ResumeForm'
import { useResumeWorkflow } from './hooks/useResumeWorkflow'
import type { ResumeFormValues } from './types/resume'

function App() {
  const {
    activeRefineSection,
    activeThemeId,
    closeRefinePanel,
    currentJob,
    fieldErrors,
    formValues,
    isPolling,
    isRegeneratingSection,
    isSubmitting,
    pageError,
    pdfPreviewUrl,
    refineValues,
    setFieldErrors,
    setFormValues,
    setRefineValues,
    openRefinePanel,
    submit,
    submitRegeneration,
  } = useResumeWorkflow()

  const updateField = (field: keyof ResumeFormValues, value: string) => {
    setFieldErrors((current) => ({ ...current, [field]: '' }))
    setFormValues((current) => ({ ...current, [field]: value }))
  }

  const updateBasicInfoField = (
    field: keyof ResumeFormValues['basicInfo'],
    value: string,
  ) => {
    setFormValues((current) => ({
      ...current,
      basicInfo: {
        ...current.basicInfo,
        [field]: value,
      },
    }))
  }

  return (
    <AppShell themeId={activeThemeId}>
      <section className="workspace-shell">
        <aside className="control-rail">
          <HeroPanel />
          <ResumeForm
            errors={fieldErrors}
            isSubmitting={isSubmitting}
            onBasicInfoChange={updateBasicInfoField}
            onChange={updateField}
            onSubmit={() => {
              void submit()
            }}
            onThemeChange={(themeId) => {
              setFormValues((current) => ({ ...current, themeId }))
            }}
            values={formValues}
          />
          <JobStatusCard isPolling={isPolling} job={currentJob} pageError={pageError} />
        </aside>

        <section className="preview-stage">
          <PdfPreviewPanel
            isRegeneratingSection={isRegeneratingSection}
            job={currentJob}
            onOpenRefine={openRefinePanel}
            onQuickRegenerate={(section) => {
              void submitRegeneration(section)
            }}
            pdfPreviewUrl={pdfPreviewUrl}
          />
        </section>
      </section>

      <RefineDrawer
        activeSection={activeRefineSection}
        isSubmitting={Boolean(isRegeneratingSection)}
        onChange={setRefineValues}
        onClose={closeRefinePanel}
        onSubmit={() => {
          if (!activeRefineSection) {
            return
          }
          void submitRegeneration(activeRefineSection, refineValues)
        }}
        values={refineValues}
      />
    </AppShell>
  )
}

export default App
