import React from 'react';
import { 
  Compass, 
  SplitSquareVertical, 
  Clock, 
  Anchor, 
  Navigation, 
  Spline, 
  ActivitySquare
} from 'lucide-react';
import type { AnalysisMode } from '../../types';
import { useAnalysis } from '../../context/AnalysisContext';

interface AnalysisModeSelectorProps {
  currentMode?: AnalysisMode;
  onSelectMode?: (mode: AnalysisMode) => void;
  hasVectors?: boolean;
  hasMultipleVars?: boolean;
}

export const AnalysisModeSelector: React.FC<AnalysisModeSelectorProps> = ({
  currentMode: propMode,
  onSelectMode: propSelect,
  hasVectors: propVectors,
  hasMultipleVars: propMulti,
}) => {
  const context = useAnalysis();
  
  const currentMode = propMode ?? context.analysisMode;
  const onSelectMode = propSelect ?? context.setAnalysisMode;
  const hasVectors = propVectors ?? (context.variables.some((v) => ['u', 'uo', 'water_u'].includes((v.name || v.variable_name || '').toLowerCase())));
  const hasMultipleVars = propMulti ?? (context.variables.length > 1);

  const modes: { id: AnalysisMode; label: string; icon: React.ReactNode; enabled: boolean; badge?: string; tooltip: string }[] = [
    {
      id: 'explore',
      label: 'Explore',
      icon: <Compass size={14} />,
      enabled: true,
      tooltip: 'Spatial 2D map exploration across space and coordinates',
    },
    {
      id: 'compare',
      label: 'Compare',
      icon: <SplitSquareVertical size={14} />,
      enabled: hasMultipleVars,
      badge: 'X vs Y',
      tooltip: 'Compare two oceanographic variables with scatter & difference maps',
    },
    {
      id: 'timeseries',
      label: 'Time',
      icon: <Clock size={14} />,
      enabled: true,
      tooltip: 'Probe temporal evolution and time series at selected location',
    },
    {
      id: 'profile',
      label: 'Depth',
      icon: <Anchor size={14} />,
      enabled: true,
      tooltip: 'Explore vertical water column sounding and thermocline structure',
    },
    {
      id: 'currents',
      label: 'Currents',
      icon: <Navigation size={14} />,
      enabled: hasVectors,
      badge: hasVectors ? 'U/V Vectors' : undefined,
      tooltip: 'Inspect hydrodynamic velocity vectors and directional flow distribution',
    },
    {
      id: 'transect',
      label: 'Transect',
      icon: <Spline size={14} />,
      enabled: true,
      badge: 'A → B',
      tooltip: 'Great-circle vertical cross-section across two endpoints',
    },
    {
      id: 'anomaly',
      label: 'Anomaly',
      icon: <ActivitySquare size={14} />,
      enabled: true,
      tooltip: 'Evaluate deviations and departures from regional baseline climatology',
    },
  ];

  return (
    <nav 
      aria-label="Analysis Modes"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.375rem',
        padding: '0.375rem',
        backgroundColor: 'var(--bg-deep)',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-default)',
        overflowX: 'auto',
        maxWidth: '100%',
      }}
    >
      {modes.map((m) => {
        const isActive = currentMode === m.id;
        return (
          <button
            key={m.id}
            onClick={() => m.enabled && onSelectMode(m.id)}
            disabled={!m.enabled}
            title={m.enabled ? m.tooltip : 'Requires multiple variables or vector components'}
            aria-pressed={isActive}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.375rem',
              padding: '0.375rem 0.625rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              fontWeight: isActive ? 600 : 400,
              cursor: m.enabled ? 'pointer' : 'not-allowed',
              opacity: m.enabled ? 1 : 0.4,
              border: isActive ? '1px solid var(--border-focus)' : '1px solid transparent',
              backgroundColor: isActive ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease',
            }}
          >
            {m.icon}
            <span>{m.label}</span>
            {m.badge && (
              <span style={{
                fontSize: '0.625rem',
                padding: '0.0625rem 0.3125rem',
                borderRadius: '2px',
                backgroundColor: isActive ? 'rgba(56, 189, 248, 0.3)' : 'rgba(255, 255, 255, 0.08)',
                color: isActive ? '#fff' : 'var(--text-muted)',
              }}>
                {m.badge}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
};
