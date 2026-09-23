import React, { useRef, useEffect, useMemo } from 'react';
import { Compass } from 'lucide-react';
import type { CurrentsAnalysisResponse, CurrentsDeliveryResponse } from '../../types';
import { useAnalysis } from '../../context/AnalysisContext';
import { EmptyState } from '../common/EmptyState';

interface VelocityStatsSummary {
  min: number | null;
  mean: number | null;
  max: number | null;
}

const computeFiniteSummary = (values: number[]): VelocityStatsSummary | null => {
  if (!values.length) return null;
  let min = values[0];
  let max = values[0];
  let sum = 0;

  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (v < min) min = v;
    if (v > max) max = v;
    sum += v;
  }

  return {
    min,
    mean: sum / values.length,
    max,
  };
};

interface CurrentsAnalysisViewerProps {
  currentsAnalysis?: CurrentsAnalysisResponse | null;
  vectorData?: CurrentsDeliveryResponse | null;
  speedThreshold?: number;
  onSpeedThresholdChange?: (val: number) => void;
}

export const CurrentsAnalysisViewer: React.FC<CurrentsAnalysisViewerProps> = ({
  currentsAnalysis: propAnalysis,
  vectorData: propVectors,
  speedThreshold: propThreshold,
  onSpeedThresholdChange: propChange,
}) => {
  const context = useAnalysis();
  const currentsAnalysis = propAnalysis !== undefined ? propAnalysis : context.currentsAnalysis;
  const vectorData = propVectors !== undefined ? propVectors : context.vectorData;
  const speedThreshold = propThreshold !== undefined ? propThreshold : context.speedThreshold;
  const onSpeedThresholdChange = propChange ?? context.setSpeedThreshold;

  const roseCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // Derived velocity statistics: Primary source is active slice vectorData.vectors, fallback to currentsAnalysis
  const { speedStats, uStats, vStats, wStats } = useMemo(() => {
    const vectors = vectorData?.vectors;
    if (vectors && vectors.length > 0) {
      const speedVals: number[] = [];
      const uVals: number[] = [];
      const vVals: number[] = [];
      const wVals: number[] = [];
      let hasValidW = false;

      for (let i = 0; i < vectors.length; i++) {
        const vec = vectors[i];

        // Prefer vector.speed calculated by backend; fallback to sqrt(u^2 + v^2 (+ w^2))
        if (typeof vec.speed === 'number' && Number.isFinite(vec.speed)) {
          speedVals.push(vec.speed);
        } else if (
          typeof vec.u === 'number' && Number.isFinite(vec.u) &&
          typeof vec.v === 'number' && Number.isFinite(vec.v)
        ) {
          const spd = typeof vec.w === 'number' && Number.isFinite(vec.w)
            ? Math.sqrt(vec.u ** 2 + vec.v ** 2 + vec.w ** 2)
            : Math.sqrt(vec.u ** 2 + vec.v ** 2);
          speedVals.push(spd);
        }

        if (typeof vec.u === 'number' && Number.isFinite(vec.u)) {
          uVals.push(vec.u);
        }
        if (typeof vec.v === 'number' && Number.isFinite(vec.v)) {
          vVals.push(vec.v);
        }
        if (typeof vec.w === 'number' && Number.isFinite(vec.w)) {
          wVals.push(vec.w);
          hasValidW = true;
        }
      }

      return {
        speedStats: computeFiniteSummary(speedVals),
        uStats: computeFiniteSummary(uVals),
        vStats: computeFiniteSummary(vVals),
        wStats: hasValidW ? computeFiniteSummary(wVals) : null,
      };
    }

    // Fallback source: Backend dataset-wide currents analysis response
    const speed = currentsAnalysis?.speed_statistics ?? currentsAnalysis?.speed;
    const u = currentsAnalysis?.component_statistics?.u ?? currentsAnalysis?.u;
    const v = currentsAnalysis?.component_statistics?.v ?? currentsAnalysis?.v;
    const w = currentsAnalysis?.component_statistics?.w ?? currentsAnalysis?.w;

    return {
      speedStats: speed ? { min: speed.min ?? null, mean: speed.mean ?? null, max: speed.max ?? null } : null,
      uStats: u ? { min: u.min ?? null, mean: u.mean ?? null, max: u.max ?? null } : null,
      vStats: v ? { min: v.min ?? null, mean: v.mean ?? null, max: v.max ?? null } : null,
      wStats: w ? { min: w.min ?? null, mean: w.mean ?? null, max: w.max ?? null } : null,
    };
  }, [vectorData, currentsAnalysis]);

  // Render Directional Flow Rose Canvas
  useEffect(() => {
    if (!vectorData || !vectorData.vectors?.length) return;

    const canvas = roseCanvasRef.current;
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

    // Clear
    ctx.fillStyle = '#0a0f1d';
    ctx.fillRect(0, 0, width, height);

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) - 25;

    // Compass Circles
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    [0.33, 0.66, 1.0].forEach((f) => {
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius * f, 0, 2 * Math.PI);
      ctx.stroke();
    });

    // Crosshairs
    ctx.beginPath();
    ctx.moveTo(centerX - radius, centerY);
    ctx.lineTo(centerX + radius, centerY);
    ctx.moveTo(centerX, centerY - radius);
    ctx.lineTo(centerX, centerY + radius);
    ctx.stroke();

    // Cardinal Labels
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText('N', centerX, centerY - radius - 4);
    ctx.textBaseline = 'top';
    ctx.fillText('S', centerX, centerY + radius + 4);
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText('E', centerX + radius + 6, centerY);
    ctx.textAlign = 'right';
    ctx.fillText('W', centerX - radius - 6, centerY);

    // Compute Directional Histogram (16 bins of 22.5 deg)
    const numBins = 16;
    const binCounts = new Array(numBins).fill(0);
    const binSpeeds = new Array(numBins).fill(0);

    const filteredVectors = vectorData.vectors.filter((v) => {
      const spd = v.speed ?? Math.sqrt((v.u || 0) ** 2 + (v.v || 0) ** 2);
      return spd >= speedThreshold;
    });

    filteredVectors.forEach((v) => {
      let deg = v.direction;
      if (deg === undefined || deg === null) {
        // Compute from u, v: oceanographic direction (degrees from North)
        deg = (Math.atan2(v.u || 0, v.v || 0) * (180 / Math.PI) + 360) % 360;
      }
      const bin = Math.floor(deg / (360 / numBins)) % numBins;
      binCounts[bin]++;
      binSpeeds[bin] += (v.speed || 0);
    });

    const maxCount = Math.max(1, ...binCounts);

    // Draw Petals
    const binAngle = (2 * Math.PI) / numBins;
    for (let i = 0; i < numBins; i++) {
      if (binCounts[i] === 0) continue;

      const angle = i * binAngle - Math.PI / 2; // start from North (top)
      const countFrac = binCounts[i] / maxCount;
      const petalLen = countFrac * radius;

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, petalLen, angle - binAngle / 2.2, angle + binAngle / 2.2);
      ctx.closePath();

      ctx.fillStyle = 'rgba(56, 189, 248, 0.45)';
      ctx.fill();
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

  }, [vectorData, speedThreshold]);

  if (!vectorData) {
    return (
      <div style={{ padding: '2rem', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <EmptyState
          icon="info"
          title="Current Velocity Data Not Active"
          description="Enable current vectors in the control panel or select a dataset with U/V velocity components."
        />
      </div>
    );
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1.2fr 1fr',
      gap: '1rem',
      width: '100%',
      height: '100%',
      backgroundColor: 'var(--bg-deep)',
      borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border-default)',
      padding: '1rem',
      boxSizing: 'border-box',
    }}>
      {/* Left: Directional Flow Rose Canvas */}
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.5rem',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
            <Compass size={14} /> DIRECTIONAL FLOW DISTRIBUTION
          </span>
          <span style={{ color: 'var(--text-muted)' }}>
            N = {vectorData.vectors?.length || 0} vectors
          </span>
        </div>

        <div style={{ flex: 1, position: 'relative', minHeight: '180px' }}>
          <canvas ref={roseCanvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
        </div>

        {/* Speed Threshold Filter */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: '0.5rem',
          padding: '0.375rem 0.5rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
        }}>
          <span style={{ color: 'var(--text-muted)' }}>Speed Cutoff:</span>
          <input
            type="range"
            min={0}
            max={vectorData.speed_max || 2}
            step={0.05}
            value={speedThreshold}
            onChange={(e) => onSpeedThresholdChange(Number(e.target.value))}
            style={{ width: '120px', accentColor: 'var(--accent-cyan)' }}
          />
          <span style={{ color: 'var(--accent-cyan)' }}>≥ {speedThreshold.toFixed(2)} m/s</span>
        </div>
      </div>

      {/* Right: Component Reductions (U, V, W, Speed) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', overflowY: 'auto' }}>
        <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 600 }}>
          VELOCITY COMPONENT STATISTICS
        </div>

        {/* Speed Magnitude */}
        <div className="surface-card" style={{ padding: '0.625rem 0.75rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>CURRENT SPEED (MAGNITUDE)</span>
            <span style={{ color: 'var(--text-muted)' }}>m/s</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.25rem', marginTop: '0.35rem', fontSize: '0.6875rem', fontFamily: 'var(--font-mono)' }}>
            <div>Min: <strong style={{ color: 'var(--text-primary)' }}>{speedStats?.min != null ? speedStats.min.toFixed(2) : '—'}</strong></div>
            <div>Mean: <strong style={{ color: 'var(--accent-emerald)' }}>{speedStats?.mean != null ? speedStats.mean.toFixed(2) : '—'}</strong></div>
            <div>Max: <strong style={{ color: 'var(--text-primary)' }}>{speedStats?.max != null ? speedStats.max.toFixed(2) : '—'}</strong></div>
          </div>
        </div>

        {/* Eastward Current U */}
        <div className="surface-card" style={{ padding: '0.625rem 0.75rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>EASTWARD CURRENT (U / UO)</span>
            <span style={{ color: 'var(--text-muted)' }}>m/s</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.25rem', marginTop: '0.35rem', fontSize: '0.6875rem', fontFamily: 'var(--font-mono)' }}>
            <div>Min: <strong>{uStats?.min != null ? uStats.min.toFixed(2) : '—'}</strong></div>
            <div>Mean: <strong>{uStats?.mean != null ? uStats.mean.toFixed(2) : '—'}</strong></div>
            <div>Max: <strong>{uStats?.max != null ? uStats.max.toFixed(2) : '—'}</strong></div>
          </div>
        </div>

        {/* Northward Current V */}
        <div className="surface-card" style={{ padding: '0.625rem 0.75rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>NORTHWARD CURRENT (V / VO)</span>
            <span style={{ color: 'var(--text-muted)' }}>m/s</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.25rem', marginTop: '0.35rem', fontSize: '0.6875rem', fontFamily: 'var(--font-mono)' }}>
            <div>Min: <strong>{vStats?.min != null ? vStats.min.toFixed(2) : '—'}</strong></div>
            <div>Mean: <strong>{vStats?.mean != null ? vStats.mean.toFixed(2) : '—'}</strong></div>
            <div>Max: <strong>{vStats?.max != null ? vStats.max.toFixed(2) : '—'}</strong></div>
          </div>
        </div>

        {/* Vertical Current W if available */}
        {wStats && (
          <div className="surface-card" style={{ padding: '0.625rem 0.75rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', fontFamily: 'var(--font-mono)' }}>
              <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>VERTICAL VELOCITY (W / WO)</span>
              <span style={{ color: 'var(--text-muted)' }}>m/s</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.25rem', marginTop: '0.35rem', fontSize: '0.6875rem', fontFamily: 'var(--font-mono)' }}>
              <div>Min: <strong>{wStats.min != null ? wStats.min.toFixed(3) : '—'}</strong></div>
              <div>Mean: <strong>{wStats.mean != null ? wStats.mean.toFixed(3) : '—'}</strong></div>
              <div>Max: <strong>{wStats.max != null ? wStats.max.toFixed(3) : '—'}</strong></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

