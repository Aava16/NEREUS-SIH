import React, { useRef, useEffect, useState } from 'react';
import type { TransectDeliveryResponse, TransectCoords } from '../../types';
import { useAnalysis } from '../../context/AnalysisContext';
import { EmptyState } from '../common/EmptyState';

interface TransectViewerProps {
  transectData?: TransectDeliveryResponse | null;
  transectCoords?: TransectCoords;
  onUpdateCoords?: (coords: Partial<TransectCoords>) => void;
  variableName?: string;
  loading?: boolean;
}

export const TransectViewer: React.FC<TransectViewerProps> = ({
  transectData: propData,
  transectCoords: propCoords,
  variableName: propVar,
}) => {
  const context = useAnalysis();
  const transectData = propData !== undefined ? propData : context.transectData;
  const transectCoords = propCoords !== undefined ? propCoords : context.transectCoords;
  const variableName = propVar ?? context.primaryVariable ?? 'Active Variable';

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<{
    dist: number;
    val: number;
    lat: number;
    lon: number;
    screenX: number;
    screenY: number;
  } | null>(null);

  useEffect(() => {
    if (!transectData || !transectData.points?.length) return;

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

    const { points, total_distance_km, min_value, max_value } = transectData;
    const validValues = points.map((p) => p.value).filter((v): v is number => v !== null && v !== undefined && isFinite(v));

    const minV = min_value !== undefined && min_value !== null ? min_value : (validValues.length ? Math.min(...validValues) : 0);
    const maxV = max_value !== undefined && max_value !== null ? max_value : (validValues.length ? Math.max(...validValues) : 1);
    const valRange = (maxV - minV) || 1;
    const maxDist = total_distance_km || 1;

    const distToX = (dist: number) => padLeft + (dist / maxDist) * plotW;
    const valToY = (val: number) => padTop + (1 - (val - minV) / valRange) * plotH;

    // Gridlines
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);

    // Y Axis Ticks (Values)
    const yTicks = 5;
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= yTicks; i++) {
      const frac = i / yTicks;
      const v = minV + frac * valRange;
      const py = padTop + (1 - frac) * plotH;
      ctx.beginPath();
      ctx.moveTo(padLeft, py);
      ctx.lineTo(padLeft + plotW, py);
      ctx.stroke();
      ctx.fillText(v.toFixed(2), padLeft - 8, py);
    }

    // X Axis Ticks (Distance in km)
    const xTicks = 6;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (let i = 0; i <= xTicks; i++) {
      const frac = i / xTicks;
      const d = frac * maxDist;
      const px = padLeft + frac * plotW;
      ctx.beginPath();
      ctx.moveTo(px, padTop);
      ctx.lineTo(px, padTop + plotH);
      ctx.stroke();
      ctx.fillText(`${d.toFixed(0)} km`, px, padTop + plotH + 6);
    }

    ctx.setLineDash([]);

    // Frame
    ctx.strokeStyle = '#2a3a5c';
    ctx.strokeRect(padLeft, padTop, plotW, plotH);

    // Plot Transect Line
    ctx.beginPath();
    let started = false;
    const validRenderPoints: { x: number; y: number; dist: number; val: number; lat: number; lon: number }[] = [];

    for (const pt of points) {
      if (pt.value === null || pt.value === undefined || !isFinite(pt.value)) continue;

      const px = distToX(pt.distance_km);
      const py = valToY(pt.value);
      validRenderPoints.push({ x: px, y: py, dist: pt.distance_km, val: pt.value, lat: pt.latitude, lon: pt.longitude });

      if (!started) {
        ctx.moveTo(px, py);
        started = true;
      } else {
        ctx.lineTo(px, py);
      }
    }

    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Area below line
    if (validRenderPoints.length > 1) {
      ctx.lineTo(validRenderPoints[validRenderPoints.length - 1].x, padTop + plotH);
      ctx.lineTo(validRenderPoints[0].x, padTop + plotH);
      ctx.closePath();
      ctx.fillStyle = 'rgba(56, 189, 248, 0.08)';
      ctx.fill();
    }

    // Points Markers
    validRenderPoints.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, 2 * Math.PI);
      ctx.fillStyle = '#38bdf8';
      ctx.fill();
    });

  }, [transectData]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!transectData || !transectData.points?.length) return;
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
      const targetDist = normX * (transectData.total_distance_km || 1);

      let nearest = transectData.points[0];
      let minDiff = Infinity;
      for (const pt of transectData.points) {
        const diff = Math.abs(pt.distance_km - targetDist);
        if (diff < minDiff && pt.value !== null && pt.value !== undefined) {
          minDiff = diff;
          nearest = pt;
        }
      }

      if (nearest && nearest.value !== null && nearest.value !== undefined) {
        setHoveredPoint({
          dist: nearest.distance_km,
          val: nearest.value,
          lat: nearest.latitude,
          lon: nearest.longitude,
          screenX: mouseX,
          screenY: mouseY,
        });
      }
    } else {
      setHoveredPoint(null);
    }
  };

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
      {/* Transect Endpoint Coordinates Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.625rem 1rem',
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.75rem',
        flexWrap: 'wrap',
        gap: '0.75rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
            <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>POINT A:</span>
            <span style={{ color: 'var(--text-secondary)' }}>
              ({transectCoords.lat1.toFixed(2)}°N, {transectCoords.lon1.toFixed(2)}°E)
            </span>
          </div>
          <span style={{ color: 'var(--border-default)' }}>→</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
            <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>POINT B:</span>
            <span style={{ color: 'var(--text-secondary)' }}>
              ({transectCoords.lat2.toFixed(2)}°N, {transectCoords.lon2.toFixed(2)}°E)
            </span>
          </div>
        </div>

        {transectData && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Length: </span>
              <strong style={{ color: 'var(--text-primary)' }}>{transectData.total_distance_km.toFixed(1)} km</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Samples: </span>
              <strong style={{ color: 'var(--text-secondary)' }}>{transectData.total_points}</strong>
            </div>
          </div>
        )}
      </div>

      {/* Canvas */}
      <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
        {!transectData || !transectData.points?.length ? (
          <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <EmptyState
              icon="info"
              title="Generating Transect Cross-Section"
              description="Sampling along great-circle path from Point A to Point B..."
            />
          </div>
        ) : (
          <canvas
            ref={canvasRef}
            style={{ width: '100%', height: '100%', display: 'block', cursor: 'crosshair' }}
            onMouseMove={handleMouseMove}
            onMouseLeave={() => setHoveredPoint(null)}
          />
        )}

        {/* Hover Tooltip */}
        {hoveredPoint && (
          <div style={{
            position: 'absolute',
            top: `${hoveredPoint.screenY - 45}px`,
            left: `${hoveredPoint.screenX + 15}px`,
            backgroundColor: 'rgba(10, 15, 29, 0.95)',
            border: '1px solid var(--border-focus)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.375rem 0.625rem',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.6875rem',
            pointerEvents: 'none',
            zIndex: 10,
            whiteSpace: 'nowrap',
          }}>
            <div>Dist: <strong>{hoveredPoint.dist.toFixed(1)} km</strong></div>
            <div>Value ({variableName}): <strong style={{ color: 'var(--accent-cyan)' }}>{hoveredPoint.val.toFixed(3)} {transectData?.units}</strong></div>
            <div style={{ color: 'var(--text-muted)' }}>({hoveredPoint.lat.toFixed(2)}°N, {hoveredPoint.lon.toFixed(2)}°E)</div>
          </div>
        )}
      </div>
    </div>
  );
};
