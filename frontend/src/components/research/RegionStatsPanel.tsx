import React from 'react';
import { 
  BoxSelect, 
  X 
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';

export const RegionStatsPanel: React.FC = () => {
  const {
    regionBounds,
    clearRegionBounds,
    gridData,
  } = useAnalysis();

  if (!regionBounds) return null;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0.5rem 0.875rem',
      backgroundColor: 'rgba(56, 189, 248, 0.1)',
      border: '1px solid var(--border-focus)',
      borderRadius: 'var(--radius-sm)',
      fontFamily: 'var(--font-mono)',
      fontSize: '0.75rem',
      gap: '0.75rem',
      flexWrap: 'wrap',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <BoxSelect size={14} className="text-accent-cyan" />
        <span style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>REGIONAL SUBSET:</span>
        <span style={{ color: 'var(--text-primary)' }}>
          [{regionBounds.minLat.toFixed(2)}° to {regionBounds.maxLat.toFixed(2)}°N, {regionBounds.minLon.toFixed(2)}° to {regionBounds.maxLon.toFixed(2)}°E]
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: 'var(--text-secondary)' }}>
        {gridData && (
          <>
            <span>Grid Cells: <strong style={{ color: 'var(--accent-emerald)' }}>{(gridData.latitudes?.length || 0) * (gridData.longitudes?.length || 0)}</strong></span>
            {gridData.min_value !== undefined && gridData.min_value !== null && (
              <span>Min: <strong style={{ color: 'var(--text-primary)' }}>{gridData.min_value.toFixed(3)}</strong></span>
            )}
            {gridData.max_value !== undefined && gridData.max_value !== null && (
              <span>Max: <strong style={{ color: 'var(--text-primary)' }}>{gridData.max_value.toFixed(3)}</strong></span>
            )}
          </>
        )}

        <button
          onClick={clearRegionBounds}
          title="Clear regional subset and return to global bounds"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.25rem',
            padding: '0.2rem 0.5rem',
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--accent-rose)',
            cursor: 'pointer',
            fontSize: '0.6875rem',
          }}
        >
          <X size={12} /> Clear Region
        </button>
      </div>
    </div>
  );
};
