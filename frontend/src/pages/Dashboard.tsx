import React, { useState } from 'react';
import { Header } from '../components/layout/Header';
import { LeftControlPanel } from '../components/controls/LeftControlPanel';
import { RightInfoPanel } from '../components/info/RightInfoPanel';
import { AnalysisModeSelector } from '../components/analysis/AnalysisModeSelector';
import { VariableComparisonViewer } from '../components/analysis/VariableComparisonViewer';
import { TransectViewer } from '../components/analysis/TransectViewer';
import { AnomalyViewer } from '../components/analysis/AnomalyViewer';
import { CurrentsAnalysisViewer } from '../components/analysis/CurrentsAnalysisViewer';
import { ScientificMapCanvas } from '../components/visualization/ScientificMapCanvas';
import { DepthProfileViewer } from '../components/visualization/DepthProfileViewer';
import { TimeSeriesViewer } from '../components/visualization/TimeSeriesViewer';
import { DifferenceViewer } from '../components/research/DifferenceViewer';
import { TimePlayerControls } from '../components/research/TimePlayerControls';
import { RegionStatsPanel } from '../components/research/RegionStatsPanel';
import { SnapshotModal } from '../components/research/SnapshotModal';
import { AnnotationDrawer } from '../components/research/AnnotationDrawer';
import { ProvenanceModal } from '../components/research/ProvenanceModal';
import { ExportModal } from '../components/research/ExportModal';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { AnalysisProvider, useAnalysis } from '../context/AnalysisContext';

const DashboardContent: React.FC = () => {
  const {
    datasets,
    datasetId,
    setDatasetId,
    primaryVariable,
    variables,
    analysisMode,
    colormap,
    setColormap,
    showVectors,
    speedThreshold,
    probeLat,
    probeLon,
    setProbeCoords,
    transectCoords,
    gridData,
    vectorData,
    profileData,
    timeseriesData,
    loading,
    error,
    refreshAll,
  } = useAnalysis();

  const [bottomDockMode, setBottomDockMode] = useState<'profile' | 'timeseries'>('profile');
  const [compareSubView, setCompareSubView] = useState<'scatter' | 'difference'>('scatter');

  const activeVarInfo = variables.find((v) => (v.name || v.variable_name) === primaryVariable) || null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Top Header with Embedded Research Actions */}
      <Header
        datasets={datasets}
        selectedDatasetId={datasetId}
        onSelectDataset={setDatasetId}
      />

      {/* Global Error Banner */}
      {error && (
        <div style={{ padding: '0 1rem' }}>
          <ErrorBanner message={error} onRetry={refreshAll} />
        </div>
      )}

      {/* Main Workspace */}
      {loading.datasets ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <LoadingSkeleton type="grid" label="Connecting to NEREUS Scientific Pipeline..." />
        </div>
      ) : datasets.length === 0 ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
          <EmptyState
            variant="card"
            title="No Scientific Datasets Registered"
            description="The NEREUS PostgreSQL catalog currently contains no registered oceanographic datasets. Datasets can be registered via the ingestion API or catalog services."
            actionLabel="Refresh Catalog"
            onAction={refreshAll}
          />
        </div>
      ) : (
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Left Control Panel */}
          <LeftControlPanel />

          {/* Central Analytics Canvas Area */}
          <main style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            backgroundColor: 'var(--bg-abyss)',
            padding: '0.75rem',
            gap: '0.625rem',
          }}>
            {/* Top Toolbar: Analysis Mode Selector + Time Player Controls */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
              <AnalysisModeSelector />
              <TimePlayerControls />
            </div>

            {/* Regional Bounding Box Selection Active Banner */}
            <RegionStatsPanel />

            {/* Dynamic Viewport Based on Mode */}
            {analysisMode === 'explore' && (
              <>
                {/* 2D Spatial Map Canvas */}
                <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
                  {loading.grid && (
                    <div style={{
                      position: 'absolute',
                      inset: 0,
                      backgroundColor: 'rgba(6, 9, 17, 0.7)',
                      backdropFilter: 'blur(2px)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      zIndex: 20,
                      borderRadius: 'var(--radius-md)',
                    }}>
                      <LoadingSkeleton type="text" label="Retrieving scientific grid slice..." />
                    </div>
                  )}
                  <ScientificMapCanvas
                    gridData={gridData}
                    vectorData={vectorData}
                    colormap={colormap}
                    onColormapChange={setColormap}
                    selectedVariable={primaryVariable || '—'}
                    units={activeVarInfo?.units || ''}
                    onCoordinateSelect={setProbeCoords}
                    selectedLat={probeLat}
                    selectedLon={probeLon}
                    showVectors={showVectors}
                    speedThreshold={speedThreshold}
                    analysisMode={analysisMode}
                  />
                </div>

                {/* Bottom Probe Dock (Height: 220px) */}
                <div style={{
                  height: '220px',
                  minHeight: '190px',
                  backgroundColor: 'var(--bg-deep)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                }}>
                  {/* Dock Tab Selector */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.35rem 0.75rem',
                    backgroundColor: 'rgba(15, 23, 42, 0.8)',
                    borderBottom: '1px solid var(--border-subtle)',
                  }}>
                    <span style={{ fontSize: '0.6875rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      PROBE COORDINATES: {probeLat !== null && probeLon !== null ? `${probeLat.toFixed(2)}°N, ${probeLon.toFixed(2)}°E` : 'Click Map to Probe'}
                    </span>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                      <button
                        onClick={() => setBottomDockMode('profile')}
                        style={{
                          padding: '0.2rem 0.5rem',
                          fontSize: '0.6875rem',
                          fontFamily: 'var(--font-mono)',
                          border: 'none',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          backgroundColor: bottomDockMode === 'profile' ? 'var(--accent-blue)' : 'transparent',
                          color: bottomDockMode === 'profile' ? '#fff' : 'var(--text-secondary)',
                        }}
                      >
                        Vertical Profile
                      </button>
                      <button
                        onClick={() => setBottomDockMode('timeseries')}
                        style={{
                          padding: '0.2rem 0.5rem',
                          fontSize: '0.6875rem',
                          fontFamily: 'var(--font-mono)',
                          border: 'none',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          backgroundColor: bottomDockMode === 'timeseries' ? 'var(--accent-blue)' : 'transparent',
                          color: bottomDockMode === 'timeseries' ? '#fff' : 'var(--text-secondary)',
                        }}
                      >
                        Time Series
                      </button>
                    </div>
                  </div>

                  <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                    {bottomDockMode === 'profile' ? (
                      <DepthProfileViewer profileData={profileData} loading={loading.profile} />
                    ) : (
                      <TimeSeriesViewer timeseriesData={timeseriesData} loading={loading.timeseries} />
                    )}
                  </div>
                </div>
              </>
            )}

            {analysisMode === 'compare' && (
              <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {/* Comparison Subview Selector */}
                <div style={{ display: 'flex', gap: '0.375rem', padding: '0.25rem' }}>
                  <button
                    onClick={() => setCompareSubView('scatter')}
                    style={{
                      padding: '0.3rem 0.75rem',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.75rem',
                      fontFamily: 'var(--font-mono)',
                      border: compareSubView === 'scatter' ? '1px solid var(--border-focus)' : '1px solid var(--border-subtle)',
                      backgroundColor: compareSubView === 'scatter' ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-deep)',
                      color: compareSubView === 'scatter' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                    }}
                  >
                    Scatter Plot & Correlation (X vs Y)
                  </button>
                  <button
                    onClick={() => setCompareSubView('difference')}
                    style={{
                      padding: '0.3rem 0.75rem',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.75rem',
                      fontFamily: 'var(--font-mono)',
                      border: compareSubView === 'difference' ? '1px solid var(--border-focus)' : '1px solid var(--border-subtle)',
                      backgroundColor: compareSubView === 'difference' ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-deep)',
                      color: compareSubView === 'difference' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                    }}
                  >
                    Difference Map (Δ = A − B)
                  </button>
                </div>

                <div style={{ flex: 1, minHeight: 0 }}>
                  {compareSubView === 'scatter' ? <VariableComparisonViewer /> : <DifferenceViewer />}
                </div>
              </div>
            )}

            {analysisMode === 'timeseries' && (
              <div style={{ flex: 1, minHeight: 0, backgroundColor: 'var(--bg-deep)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)', padding: '0.5rem' }}>
                <TimeSeriesViewer timeseriesData={timeseriesData} loading={loading.timeseries} />
              </div>
            )}

            {analysisMode === 'profile' && (
              <div style={{ flex: 1, minHeight: 0, backgroundColor: 'var(--bg-deep)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)', padding: '0.5rem' }}>
                <DepthProfileViewer profileData={profileData} loading={loading.profile} />
              </div>
            )}

            {analysisMode === 'currents' && (
              <div style={{ flex: 1, minHeight: 0 }}>
                <CurrentsAnalysisViewer />
              </div>
            )}

            {analysisMode === 'transect' && (
              <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {/* Embedded Mini Map for Transect Track Visualisation */}
                <div style={{ height: '240px', position: 'relative' }}>
                  <ScientificMapCanvas
                    gridData={gridData}
                    vectorData={vectorData}
                    colormap={colormap}
                    selectedVariable={primaryVariable || '—'}
                    units={activeVarInfo?.units || ''}
                    analysisMode={analysisMode}
                    transectCoords={transectCoords}
                  />
                </div>
                {/* 1D Cross-Section Plot along Transect */}
                <div style={{ flex: 1, minHeight: 0 }}>
                  <TransectViewer />
                </div>
              </div>
            )}

            {analysisMode === 'anomaly' && (
              <div style={{ flex: 1, minHeight: 0 }}>
                <AnomalyViewer />
              </div>
            )}
          </main>

          {/* Right Information & Statistics Panel */}
          <RightInfoPanel />
        </div>
      )}

      {/* Phase 11 Research Modals & Drawers */}
      <SnapshotModal />
      <AnnotationDrawer />
      <ProvenanceModal />
      <ExportModal />
    </div>
  );
};

export const Dashboard: React.FC = () => {
  return (
    <AnalysisProvider>
      <DashboardContent />
    </AnalysisProvider>
  );
};


