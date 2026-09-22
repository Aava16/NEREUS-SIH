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
  const hasVectors = propVectors ?? (context.variables.some((v) => ['u', 'uo'].includes((v.name || v.variable_name || '').toLowerCase())));
  const hasMultipleVars = propMulti ?? (context.variables.length > 1);
  const modes: { id: AnalysisMode; label: string; icon: React.ReactNode; enabled: boolean; badge?: string }[] = [
    {
      id: 'explore',
      label: 'Spatial Explore',
      icon: <Compass size={14} />,
      enabled: true,
    },
    {
      id: 'compare',
      label: 'Variable Compare',
      icon: <SplitSquareVertical size={14} />,
      enabled: hasMultipleVars,
      badge: 'X vs Y',
    },
    {
      id: 'timeseries',
      label: 'Time-Series',
      icon: <Clock size={14} />,
      enabled: true,
    },
    {
      id: 'profile',
      label: 'Depth Profile',
      icon: <Anchor size={14} />,
      enabled: true,
    },
    {
      id: 'currents',
      label: 'Currents (U/V)',
      icon: <Navigation size={14} />,
      enabled: hasVectors,
      badge: hasVectors ? 'Vector Field' : undefined,
    },
    {
      id: 'transect',
      label: 'Transect Line',
      icon: <Spline size={14} />,
      enabled: true,
      badge: 'A → B',
    },
    {
      id: 'anomaly',
      label: 'Anomaly Analysis',
      icon: <ActivitySquare size={14} />,
      enabled: true,
    },
  ];

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.375rem',
      padding: '0.375rem',
      backgroundColor: 'var(--bg-deep)',
      borderRadius: 'var(--radius-sm)',
      border: '1px solid var(--border-default)',
      overflowX: 'auto',
      maxWidth: '100%',
    }}>
      {modes.map((m) => {
        const isActive = currentMode === m.id;
        return (
          <button
            key={m.id}
            onClick={() => m.enabled && onSelectMode(m.id)}
            disabled={!m.enabled}
            title={m.enabled ? `Switch to ${m.label} mode` : 'Not supported by current dataset variables'}
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
    </div>
  );
};
