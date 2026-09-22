import React, { useRef, useEffect, useState, useMemo } from 'react';
import { Info } from 'lucide-react';
import type { GridDeliveryResponse, VariableStatistics } from '../../types';
import { useAnalysis } from '../../context/AnalysisContext';
import { EmptyState } from '../common/EmptyState';

interface VariableComparisonViewerProps {
  primaryVariable?: string | null;
  secondaryVariable?: string | null;
  primaryGrid?: GridDeliveryResponse | null;
  secondaryGrid?: GridDeliveryResponse | null;
  primaryStats?: VariableStatistics | null;
  secondaryStats?: VariableStatistics | null;
}

export const VariableComparisonViewer: React.FC<VariableComparisonViewerProps> = ({
  primaryVariable: propPrimary,
  secondaryVariable: propSecondary,
  primaryGrid: propPGrid,
  secondaryGrid: propSGrid,
}) => {
  const context = useAnalysis();
  const primaryVariable = propPrimary ?? context.primaryVariable ?? '';
  const secondaryVariable = propSecondary ?? context.secondaryVariable ?? '';
  const primaryGrid = propPGrid ?? context.gridData;
  const secondaryGrid = propSGrid ?? context.secondaryGridData;
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<{ x: number; y: number; screenX: number; screenY: number } | null>(null);

  // Compute paired data points and Pearson correlation
  const comparisonData = useMemo(() => {
    if (!primaryGrid || !secondaryGrid) return null;
    if (!primaryGrid.values?.length || !secondaryGrid.values?.length) return null;

    const numRows = Math.min(primaryGrid.values.length, secondaryGrid.values.length);
    const numCols = Math.min(primaryGrid.values[0]?.length || 0, secondaryGrid.values[0]?.length || 0);

    const pairs: [number, number][] = [];
    let sumX = 0;
    let sumY = 0;

    for (let r = 0; r < numRows; r++) {
      for (let c = 0; c < numCols; c++) {
        const x = primaryGrid.values[r]?.[c];
        const y = secondaryGrid.values[r]?.[c];
        if (x !== null && x !== undefined && y !== null && y !== undefined && npFinite(x) && npFinite(y)) {
          pairs.push([x, y]);
          sumX += x;
          sumY += y;
        }
      }
    }

    if (pairs.length < 2) return null;

    const n = pairs.length;
    const meanX = sumX / n;
    const meanY = sumY / n;

    let num = 0;
    let denX = 0;
    let denY = 0;

    for (const [x, y] of pairs) {
      const dx = x - meanX;
      const dy = y - meanY;
      num += dx * dy;
      denX += dx * dx;
      denY += dy * dy;
    }

    const denom = Math.sqrt(denX * denY);
    const r = denom === 0 ? 0 : num / denom;
    const r2 = r * r;
    const slope = denX === 0 ? 0 : num / denX;
    const intercept = meanY - slope * meanX;

    const allX = pairs.map((p) => p[0]);
    const allY = pairs.map((p) => p[1]);
    const minX = Math.min(...allX);
    const maxX = Math.max(...allX);
    const minY = Math.min(...allY);
    const maxY = Math.max(...allY);

    return {
      pairs,
      n,
      meanX,
      meanY,
      r,
      r2,
      slope,
      intercept,
      minX,
      maxX,
      minY,
      maxY,
    };
  }, [primaryGrid, secondaryGrid]);

  function npFinite(v: any): v is number {
    return typeof v === 'number' && isFinite(v) && !isNaN(v);
  }

  // Draw Scatter Plot Canvas
  useEffect(() => {
    if (!comparisonData) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Clear background
    ctx.fillStyle = '#0a0f1d';
    ctx.fillRect(0, 0, width, height);

    const padLeft = 65;
    const padRight = 30;
    const padTop = 30;
    const padBottom = 40;

    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    const { pairs, minX, maxX, minY, maxY, slope, intercept } = comparisonData;
    const rangeX = (maxX - minX) || 1;
    const rangeY = (maxY - minY) || 1;

    const xToScreen = (x: number) => padLeft + ((x - minX) / rangeX) * plotW;
    const yToScreen = (y: number) => padTop + (1 - (y - minY) / rangeY) * plotH;

    // Gridlines & Axes
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);

    // Y Axis Ticks
    const yTicks = 5;
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= yTicks; i++) {
      const frac = i / yTicks;
      const yVal = minY + frac * rangeY;
      const py = padTop + (1 - frac) * plotH;
      ctx.beginPath();
      ctx.moveTo(padLeft, py);
      ctx.lineTo(padLeft + plotW, py);
      ctx.stroke();
      ctx.fillText(yVal.toFixed(2), padLeft - 8, py);
    }

    // X Axis Ticks
    const xTicks = 6;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (let i = 0; i <= xTicks; i++) {
      const frac = i / xTicks;
      const xVal = minX + frac * rangeX;
      const px = padLeft + frac * plotW;
      ctx.beginPath();
      ctx.moveTo(px, padTop);
      ctx.lineTo(px, padTop + plotH);
      ctx.stroke();
      ctx.fillText(xVal.toFixed(2), px, padTop + plotH + 6);
    }

    ctx.setLineDash([]);

    // Frame
    ctx.strokeStyle = '#2a3a5c';
    ctx.strokeRect(padLeft, padTop, plotW, plotH);

    // Linear Regression Best-Fit Line
    ctx.beginPath();
    const regY1 = slope * minX + intercept;
    const regY2 = slope * maxX + intercept;
    ctx.moveTo(xToScreen(minX), yToScreen(regY1));
    ctx.lineTo(xToScreen(maxX), yToScreen(regY2));
    ctx.strokeStyle = 'rgba(244, 63, 94, 0.7)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Data Points (Subsample if N > 3000 to maintain 60fps)
    const stride = pairs.length > 3000 ? Math.ceil(pairs.length / 3000) : 1;
    ctx.fillStyle = 'rgba(56, 189, 248, 0.4)';

    for (let i = 0; i < pairs.length; i += stride) {
      const [x, y] = pairs[i];
      const px = xToScreen(x);
      const py = yToScreen(y);
      ctx.beginPath();
      ctx.arc(px, py, 2, 0, 2 * Math.PI);
      ctx.fill();
    }

  }, [comparisonData]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!comparisonData) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const padLeft = 65;
    const padRight = 30;
    const padTop = 30;
    const padBottom = 40;
    const plotW = rect.width - padLeft - padRight;
    const plotH = rect.height - padTop - padBottom;

    if (mouseX >= padLeft && mouseX <= padLeft + plotW && mouseY >= padTop && mouseY <= padTop + plotH) {
      const normX = (mouseX - padLeft) / plotW;
      const normY = 1 - (mouseY - padTop) / plotH;
      const targetX = comparisonData.minX + normX * (comparisonData.maxX - comparisonData.minX);
      const targetY = comparisonData.minY + normY * (comparisonData.maxY - comparisonData.minY);

      setHoveredPoint({
        x: targetX,
        y: targetY,
        screenX: mouseX,
        screenY: mouseY,
      });
    } else {
      setHoveredPoint(null);
    }
  };

  if (!primaryGrid || !secondaryGrid) {
    return (
      <div style={{ padding: '2rem', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <EmptyState
          icon="info"
          title="Select Two Variables to Compare"
          description="Choose a primary variable (X) and secondary variable (Y) from the control panel to evaluate scientific correlation."
        />
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
      {/* Top Statistical Summary Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.625rem 1rem',
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.75rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>X (Primary): </span>
            <strong style={{ color: 'var(--accent-cyan)' }}>{primaryVariable}</strong>
            <span style={{ color: 'var(--text-muted)' }}> ({primaryGrid.units || 'unitless'})</span>
          </div>
          <span style={{ color: 'var(--border-default)' }}>vs</span>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Y (Secondary): </span>
            <strong style={{ color: 'var(--accent-emerald)' }}>{secondaryVariable}</strong>
            <span style={{ color: 'var(--text-muted)' }}> ({secondaryGrid.units || 'unitless'})</span>
          </div>
        </div>

        {comparisonData && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Pearson r: </span>
              <strong style={{ color: Math.abs(comparisonData.r) > 0.5 ? 'var(--accent-emerald)' : 'var(--text-primary)' }}>
                {comparisonData.r.toFixed(4)}
              </strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>R²: </span>
              <strong style={{ color: 'var(--text-primary)' }}>{comparisonData.r2.toFixed(4)}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>N: </span>
              <span style={{ color: 'var(--text-secondary)' }}>{comparisonData.n.toLocaleString()} cells</span>
            </div>
          </div>
        )}
      </div>

      {/* Main Canvas Area */}
      <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
        <canvas
          ref={canvasRef}
          style={{ width: '100%', height: '100%', display: 'block', cursor: 'crosshair' }}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoveredPoint(null)}
        />

        {/* Hover Coordinate Tag */}
        {hoveredPoint && (
          <div style={{
            position: 'absolute',
            bottom: '12px',
            right: '12px',
            backgroundColor: 'rgba(10, 15, 29, 0.95)',
            border: '1px solid var(--border-focus)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.375rem 0.625rem',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.6875rem',
            pointerEvents: 'none',
            zIndex: 10,
          }}>
            <div>X ({primaryVariable}): <strong>{hoveredPoint.x.toFixed(3)}</strong></div>
            <div>Y ({secondaryVariable}): <strong>{hoveredPoint.y.toFixed(3)}</strong></div>
          </div>
        )}
      </div>

      {/* Scientific Caveat Footer */}
      <div style={{
        padding: '0.375rem 1rem',
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        borderTop: '1px solid var(--border-subtle)',
        fontSize: '0.6875rem',
        color: 'var(--text-muted)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.375rem',
      }}>
        <Info size={12} color="var(--accent-cyan)" />
        <span>Statistical correlation coefficient reflects co-variation across spatial cells. It does not establish causal ocean dynamics.</span>
      </div>
    </div>
  );
};
