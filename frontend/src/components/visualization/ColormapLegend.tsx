import React from 'react';
import { type ColormapName, COLORMAP_NAMES, getColorHex } from '../../utils/colormaps';

interface ColormapLegendProps {
  variableName: string;
  units: string;
  min: number;
  max: number;
  colormap: ColormapName;
  onColormapChange?: (name: ColormapName) => void;
  orientation?: 'horizontal' | 'vertical';
}

export const ColormapLegend: React.FC<ColormapLegendProps> = ({
  variableName,
  units,
  min,
  max,
  colormap,
  onColormapChange,
  orientation = 'horizontal',
}) => {
  // Generate a multi-stop CSS gradient from the chosen colormap
  const gradientStops = Array.from({ length: 11 }, (_, i) => {
    const t = i / 10;
    const hex = getColorHex(t, colormap);
    return `${hex} ${t * 100}%`;
  }).join(', ');

  const formatVal = (val: number) => {
    if (isNaN(val) || !isFinite(val)) return '—';
    if (Math.abs(val) < 0.01 && val !== 0) return val.toExponential(2);
    if (Math.abs(val) >= 10000) return val.toExponential(2);
    return val.toFixed(2);
  };

  const mid = min + (max - min) / 2;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '0.375rem',
      padding: '0.625rem 0.875rem',
      backgroundColor: 'rgba(10, 15, 29, 0.85)',
      backdropFilter: 'blur(8px)',
      border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-sm)',
      boxShadow: 'var(--shadow-md)',
      color: 'var(--text-primary)',
      minWidth: '240px',
      fontSize: '0.75rem',
      fontFamily: 'var(--font-mono)',
    }}>
      {/* Legend Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
        <span style={{ fontWeight: 600, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
          {variableName} <span style={{ color: 'var(--text-muted)' }}>({units || 'unitless'})</span>
        </span>
        {onColormapChange && (
          <select
            value={colormap}
            onChange={(e) => onColormapChange(e.target.value as ColormapName)}
            style={{
              fontSize: '0.6875rem',
              fontFamily: 'var(--font-mono)',
              padding: '0.125rem 0.375rem',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
            }}
          >
            {COLORMAP_NAMES.map((cm) => (
              <option key={cm} value={cm}>
                {cm.toUpperCase()}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Colormap Bar */}
      <div
        style={{
          width: '100%',
          height: orientation === 'horizontal' ? '12px' : '120px',
          borderRadius: '2px',
          background: `linear-gradient(to right, ${gradientStops})`,
          border: '1px solid rgba(255, 255, 255, 0.2)',
          position: 'relative',
        }}
      />

      {/* Value Ticks */}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', color: 'var(--text-secondary)' }}>
        <span>{formatVal(min)}</span>
        <span>{formatVal(mid)}</span>
        <span>{formatVal(max)}</span>
      </div>

      {/* NaN Indicator */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.375rem',
        marginTop: '0.125rem',
        fontSize: '0.625rem',
        color: 'var(--text-muted)',
      }}>
        <div style={{
          width: '10px',
          height: '10px',
          backgroundColor: '#334155',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: '1px',
        }} />
        <span>Masked / NaN</span>
      </div>
    </div>
  );
};
