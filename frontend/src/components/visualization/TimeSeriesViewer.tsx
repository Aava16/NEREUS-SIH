import React, { useRef, useEffect, useState } from 'react';
import type { TimeSeriesDeliveryResponse, TimeSeriesPoint } from '../../types';
import { EmptyState } from '../common/EmptyState';
import { getVariableDisplay } from '../../utils/variableNames';

interface TimeSeriesViewerProps {
  timeseriesData: TimeSeriesDeliveryResponse | null;
  loading?: boolean;
}

export const TimeSeriesViewer: React.FC<TimeSeriesViewerProps> = ({
  timeseriesData,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<{
    time: string;
    val: number;
    screenX: number;
    screenY: number;
  } | null>(null);

  useEffect(() => {
    if (!timeseriesData) return;

    // Harmonize timestamps & values
    const timestamps = timeseriesData.timestamps || timeseriesData.points?.map((p: TimeSeriesPoint) => p.timestamp) || [];
    const values = timeseriesData.values || timeseriesData.points?.map((p: TimeSeriesPoint) => p.value ?? null) || [];

    if (!timestamps.length || !values.length) return;

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

    const padLeft = 60;
    const padRight = 30;
    const padTop = 30;
    const padBottom = 30;

    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    const { min_value, max_value } = timeseriesData;

    const validValues = values.filter((v: number | null): v is number => v !== null && !isNaN(v));
    const minVal = min_value !== undefined ? min_value : (validValues.length ? Math.min(...validValues) : 0);
    const maxVal = max_value !== undefined ? max_value : (validValues.length ? Math.max(...validValues) : 1);
    const valRange = (maxVal - minVal) || 1;
    const numPoints = timestamps.length;

    // Time goes left to right
    const idxToX = (idx: number) => {
      const norm = idx / Math.max(1, numPoints - 1);
      return padLeft + norm * plotW;
    };

    // Value goes bottom to top
    const valToY = (val: number) => {
      const norm = (val - minVal) / valRange;
      return padTop + (1 - norm) * plotH;
    };

    // Draw Gridlines & Axes
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);

    // Value Y ticks
    const yTicks = 5;
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';

    for (let i = 0; i <= yTicks; i++) {
      const frac = i / yTicks;
      const v = minVal + frac * valRange;
      const y = padTop + (1 - frac) * plotH;

      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(padLeft + plotW, y);
      ctx.stroke();

      ctx.fillText(v.toFixed(2), padLeft - 8, y);
    }

    // Time X ticks
    const xTicks = Math.min(6, numPoints);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    for (let i = 0; i < xTicks; i++) {
      const idx = Math.round((i / (xTicks - 1 || 1)) * (numPoints - 1));
      const x = idxToX(idx);
      const timeStr = timestamps[idx];
      const shortTime = timeStr ? timeStr.split('T')[0] : `T${idx}`;

      ctx.beginPath();
      ctx.moveTo(x, padTop);
      ctx.lineTo(x, padTop + plotH);
      ctx.stroke();

      ctx.fillText(shortTime, x, padTop + plotH + 6);
    }

    ctx.setLineDash([]);

    // Frame
    ctx.strokeStyle = '#2a3a5c';
    ctx.strokeRect(padLeft, padTop, plotW, plotH);

    // Plot Line
    ctx.beginPath();
    let started = false;
    const validPoints: { time: string; val: number; x: number; y: number }[] = [];

    for (let i = 0; i < numPoints; i++) {
      const val = values[i];
      if (val === null || isNaN(val)) continue;

      const x = idxToX(i);
      const y = valToY(val);
      validPoints.push({ time: timestamps[i], val, x, y });

      if (!started) {
        ctx.moveTo(x, y);
        started = true;
      } else {
        ctx.lineTo(x, y);
      }
    }

    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Area fill below line
    if (validPoints.length > 1) {
      ctx.lineTo(validPoints[validPoints.length - 1].x, padTop + plotH);
      ctx.lineTo(validPoints[0].x, padTop + plotH);
      ctx.closePath();
      ctx.fillStyle = 'rgba(16, 185, 129, 0.08)';
      ctx.fill();
    }

    // Draw point dots
    validPoints.forEach((pt) => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 3, 0, 2 * Math.PI);
      ctx.fillStyle = '#10b981';
      ctx.fill();
    });

  }, [timeseriesData]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!timeseriesData) return;
    const timestamps = timeseriesData.timestamps || timeseriesData.points?.map((p: TimeSeriesPoint) => p.timestamp) || [];
    const values = timeseriesData.values || timeseriesData.points?.map((p: TimeSeriesPoint) => p.value ?? null) || [];

    if (!timestamps.length) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const padLeft = 60;
    const padRight = 30;
    const padTop = 30;
    const padBottom = 30;
    const plotW = rect.width - padLeft - padRight;
    const plotH = rect.height - padTop - padBottom;

    if (mouseX >= padLeft && mouseX <= padLeft + plotW && mouseY >= padTop && mouseY <= padTop + plotH) {
      const normX = (mouseX - padLeft) / plotW;
      const targetIdx = Math.round(normX * (timestamps.length - 1));
      const val = values[targetIdx];

      if (val !== null && val !== undefined) {
        setHoveredPoint({
          time: timestamps[targetIdx],
          val,
          screenX: mouseX,
          screenY: mouseY,
        });
      }
    } else {
      setHoveredPoint(null);
    }
  };

  if (!timeseriesData) {
    return (
      <div style={{ padding: '1rem', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <EmptyState
          icon="info"
          title="Select a point on the map to explore temporal trends"
          description="Click any coordinate on the spatial map to inspect how oceanographic variables evolve across available time steps."
        />
      </div>
    );
  }

  const rawVar = timeseriesData.variable || timeseriesData.variable_name;
  const varDisplay = getVariableDisplay(rawVar);

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      height: '100%',
      minHeight: '220px',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header Info */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.375rem 0.75rem',
        borderBottom: '1px solid var(--border-subtle)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.6875rem',
        color: 'var(--text-secondary)',
      }}>
        <div>
          <strong style={{ color: 'var(--accent-emerald)' }}>TIME-SERIES</strong>: {varDisplay.label} ({rawVar}) {timeseriesData.units ? `[${timeseriesData.units}]` : ''}
        </div>
        <div>
          LAT: {(timeseriesData.lat ?? timeseriesData.latitude ?? 0).toFixed(2)}° | LON: {(timeseriesData.lon ?? timeseriesData.longitude ?? 0).toFixed(2)}° | DEPTH: {timeseriesData.depth ?? 0}m
        </div>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: 'calc(100% - 28px)', display: 'block' }}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoveredPoint(null)}
      />

      {/* Hover Tooltip */}
      {hoveredPoint && (
        <div style={{
          position: 'absolute',
          top: `${hoveredPoint.screenY - 30}px`,
          left: `${hoveredPoint.screenX + 15}px`,
          backgroundColor: 'rgba(10, 15, 29, 0.95)',
          border: '1px solid var(--border-focus)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.25rem 0.5rem',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.6875rem',
          pointerEvents: 'none',
          zIndex: 10,
          whiteSpace: 'nowrap',
        }}>
          <div>Time: <strong style={{ color: 'var(--accent-cyan)' }}>{hoveredPoint.time}</strong></div>
          <div>Value: <strong style={{ color: 'var(--accent-emerald)' }}>{hoveredPoint.val.toFixed(3)} {timeseriesData.units}</strong></div>
        </div>
      )}
    </div>
  );
};
