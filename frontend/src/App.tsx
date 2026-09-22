import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import { Dashboard } from './pages/Dashboard';
import { DatasetExplorer } from './pages/DatasetExplorer';
import { DatasetDetail } from './pages/DatasetDetail';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/workspace" element={<Dashboard />} />
        <Route path="/datasets" element={<DatasetExplorer />} />
        <Route path="/datasets/:id" element={<DatasetDetail />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
