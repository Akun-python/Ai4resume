import type { PropsWithChildren } from 'react'

import type { ThemeId } from '../types/resume'

interface AppShellProps extends PropsWithChildren {
  themeId: ThemeId
}

export const AppShell = ({ children, themeId }: AppShellProps) => (
  <div className="app-shell" data-theme={themeId}>
    <main className="workspace">{children}</main>
  </div>
)
