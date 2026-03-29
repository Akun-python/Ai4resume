import { Route, Routes } from 'react-router-dom'

import App from '../App'

export const AppRouter = () => (
  <Routes>
    <Route element={<App />} path="/" />
  </Routes>
)
