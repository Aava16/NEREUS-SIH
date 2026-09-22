import React, { useRef, useEffect, useMemo } from 'react';
import { 
  GitCompare, 
  AlertTriangle 
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';
import { getColorRgba } from '../../utils/colormaps';
import { EmptyState } from '../common/EmptyState';

export const DifferenceViewer: React.FC = () => {
  const {
    gridData,
    secondaryGridData,
    primaryVariable,
    secondaryVariable,
    variables,
  } = useAnalysis();

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const primaryVarInfo = variables.find((v) => (v.name || v.variable_name) === primaryVariable);
  const secondaryVarInfo = variables.find((v) => (v.name || v.variable_name) === secondaryVariable);

  // Check scientific compatibility (units and dimensional compatibility)
  const isCompatible = useMemo(() => {
    if (!primaryVarInfo || !secondaryVarInfo) return false;
    const u1 = (primaryVarInfo.units || '').trim().toLowerCase();
    const u2 = (secondaryVarInfo.units || '').trim().toLowerCase();
    return u1 === u2 || (u1 === '' && u2 === '');
  }, [primaryVarInfo, secondaryVarInfo]);

  // Compute Difference Grid Matrix (Delta = A - B)
  const diffGrid = useMemo(() => {
    if (!gridData || !secondaryGridData || !gridData.values?.length || !secondaryGridData.values?.length) return null;

    const rows = Math.min(gridData.values.length, secondaryGridData.values.length);
    const cols = Math.min(gridData.values[0]?.length || 0, secondaryGridData.values[0]?.length || 0);

    const diffs: (number | null)[][] = [];
    let minDelta = Infinity;
    let maxDelta = -Infinity;
    let maxAbs = 0;
    let validCount = 0;

    for (let r = 0; r < rows; r++) {
      const row: (number | null)[] = [];
      for (let c = 0; c < cols; c++) {
        const vA = gridData.values[r]?.[c];
        const vB = secondaryGridData.values[r]?.[c];

        if (vA !== null && vA !== undefined && isFinite(vA) && vB !== null && vB !== undefined && isFinite(vB)) {
          const delta = vA - vB;
          row.push(delta);
          if (delta < minDelta) minDelta = delta;
          if (delta > maxDelta) maxDelta = delta;
          if (Math.abs(delta) > maxAbs) maxAbs = Math.abs(delta);
          validCount++;
        } else {
          row.push(null);
        }
      }
      diffs.push(row);
    }

    if (validCount === 0) return null;

    return {
      diffs,
      rows,
      cols,
      minDelta,
      maxDelta,
      maxAbs: maxAbs || 1.0,
      validCount,
    };
  }, [gridData, secondaryGridData]);

  // Render Diverging Difference Canvas
  useEffect(() => {
    if (!diffGrid || !gridData) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { rows, cols, diffs, maxAbs } = diffGrid;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Clear background
    ctx.fillStyle = '#060911';
    ctx.fillRect(0, 0, width, height);

    // Create offscreen buffer
    const imgData = ctx.createImageData(cols, rows);
    const data = imgData.data;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const idx = (r * cols + c) * 4;
        const delta = diffs[r][c];

        if (delta === null) {
          data[idx] = 10;
          data[idx + 1] = 15;
          data[idx + 2] = 29;
          data[idx + 3] = 255;
        } else {
          // Normalize to [0, 1] with 0.5 as zero delta using diverging coolwarm
          const norm = (delta / (maxAbs * 2)) + 0.5;
          const [red, green, blue] = getColorRgba(Math.max(0, Math.min(1, norm)), 'coolwarm');
          data[idx] = red;
          data[idx + 1] = green;
          data[idx + 2] = blue;
          data[idx + 3] = 255;
        }
      }
    }

    const offscreen = document.createElement('canvas');
    offscreen.width = cols;
    offscreen.height = rows;
    const offCtx = offscreen.getContext('2d');
    if (offCtx) {
      offCtx.putImageData(imgData, 0, 0);
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(offscreen, 0, 0, width, height);
    }
  }, [diffGrid, gridData]);

  if (!secondaryVariable) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-deep)', borderRadius: 'var(--radius-md)', padding: '2rem' }}>
        <EmptyState
          icon="info"
          title="Select Secondary Variable for Difference Map"
          description="Choose a compatible secondary variable in the left control panel to compute point-by-point numerical difference (A − B)."
        />
      </div>
    );
  }

  if (!isCompatible) {
    return (
      <div style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-deep)',
        borderRadius: 'var(--radius-md)',
        padding: '2rem',
        textAlign: 'center',
        gap: '1rem',
      }}>
        <AlertTriangle size={36} className="text-accent-rose" />
        <div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.125rem', color: 'var(--text-primary)', margin: '0 0 0.5rem' }}>
            Incompatible Physical Units
          </h3>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', maxWidth: '480px', lineHeight: 1.5, margin: 0 }}>
            Cannot compute numerical difference between <strong>{primaryVariable}</strong> ({primaryVarInfo?.units || 'unitless'}) and <strong>{secondaryVariable}</strong> ({secondaryVarInfo?.units || 'unitless'}).
            Scientific difference calculation requires identical physical units.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      width: '100%',
      height: '100%',
      backgroundColor: 'var(--bg-deep)',
      borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border-default)',
      overflow: 'hidden',
    }}>
      {/* Header Info Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.625rem 1rem',
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
        fontSize: '0.75rem',
        fontFamily: 'var(--font-mono)',
        flexWrap: 'wrap',
        gap: '0.5rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <GitCompare size={14} className="text-accent-cyan" />
          <span>DELTA (Δ = {primaryVariable} − {secondaryVariable})</span>
          <span style={{ color: 'var(--accent-emerald)' }}>[{primaryVarInfo?.units || 'unitless'}]</span>
        </div>

        {diffGrid && (
          <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-secondary)' }}>
            <span>Min Δ: <strong style={{ color: 'var(--accent-blue)' }}>{diffGrid.minDelta.toFixed(3)}</strong></span>
            <span>Max Δ: <strong style={{ color: 'var(--accent-rose)' }}>+{diffGrid.maxDelta.toFixed(3)}</strong></span>
            <span>Scale Range: <strong style={{ color: 'var(--text-primary)' }}>±{diffGrid.maxAbs.toFixed(3)}</strong></span>
          </div>
        )}
      </div>

      {/* Difference Map Canvas */}
      <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
        <canvas
          ref={canvasRef}
          style={{ width: '100%', height: '100%', display: 'block' }}
        />

        {/* Diverging Colormap Legend Overlay */}
        <div style={{
          position: 'absolute',
          bottom: '12px',
          right: '12px',
          padding: '0.5rem 0.75rem',
          backgroundColor: 'rgba(10, 15, 29, 0.9)',
          backdropFilter: 'blur(4px)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.6875rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.25rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span>-Δ (B &gt; A)</span>
            <span>0.0 (Equal)</span>
            <span>+Δ (A &gt; B)</span>
          </div>
          <div style={{
            width: '180px',
            height: '10px',
            borderRadius: '2px',
            background: 'linear-gradient(to right, #3b82f6, #f8fafc, #ef4444)',
          }} />
        </div>
      </div>
    </div>
  );
};
