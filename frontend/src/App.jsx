import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './lib/ThemeContext';
import LandingPage from './pages/LandingPage';
import OnboardingPage from './pages/OnboardingPage';
import IssueFeedPage from './pages/IssueFeedPage';
import IssueWorkspacePage from './pages/IssueWorkspacePage';

export function App() {
  return (
    <ThemeProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/issues" element={<IssueFeedPage />} />
        <Route path="/issues/:id" element={<IssueWorkspacePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ThemeProvider>
  );
}

export default App;