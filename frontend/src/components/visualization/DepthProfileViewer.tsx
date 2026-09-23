import React, { useRef, useEffect, useState } from 'react';
import type { DepthProfileResponse } from '../../types';
import { EmptyState } from '../common/EmptyState';
import { getVariableDisplay } from '../../utils/variableNames';

interface DepthProfileViewerProps {
  profileData: DepthProfileResponse | null;
  loading?: boolean;
}

export const DepthProfileViewer: React.FC<DepthProfileViewerProps> = ({
  profileData,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<{
    depth: number;
    val: number;
    screenX: number;
    screenY: number;
  } | null>(null);

  useEffect(() => {
    if (!profileData || !profileData.depths?.length || !profileData.values?.length) return;

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

    const { depths, values, min_value, max_value, depth_units } = profileData;

    const minDepth = Math.min(...depths);
    const maxDepth = Math.max(...depths);
    const validValues = values.filter((v): v is number => v !== null && !isNaN(v));
    const minVal = min_value !== undefined ? min_value : (validValues.length ? Math.min(...validValues) : 0);
    const maxVal = max_value !== undefined ? max_value : (validValues.length ? Math.max(...validValues) : 1);
    const valRange = (maxVal - minVal) || 1;
    const depthRange = (maxDepth - minDepth) || 1;

    // Depth goes down (inverted axis: 0 at top, max depth at bottom)
    const depthToY = (depth: number) => {
      const norm = (depth - minDepth) / depthRange;
      return padTop + norm * plotH;
    };

    // Value goes left to right
    const valToX = (val: number) => {
      const norm = (val - minVal) / valRange;
      return padLeft + norm * plotW;
    };

    // Draw Grid & Axes
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);

    // Depth horizontal gridlines
    const depthTicks = 5;
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';

    for (let i = 0; i <= depthTicks; i++) {
      const frac = i / depthTicks;
      const d = minDepth + frac * depthRange;
      const y = depthToY(d);

      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(padLeft + plotW, y);
      ctx.stroke();

      ctx.fillText(`${d.toFixed(0)} ${depth_units || 'm'}`, padLeft - 8, y);
    }

    // Value vertical gridlines
    const valTicks = 5;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    for (let i = 0; i <= valTicks; i++) {
      const frac = i / valTicks;
      const v = minVal + frac * valRange;
      const x = padLeft + frac * plotW;

      ctx.beginPath();
      ctx.moveTo(x, padTop);
      ctx.lineTo(x, padTop + plotH);
      ctx.stroke();

      ctx.fillText(v.toFixed(2), x, padTop - 5);
    }

    ctx.setLineDash([]);

    // Draw Frame
    ctx.strokeStyle = '#2a3a5c';
    ctx.strokeRect(padLeft, padTop, plotW, plotH);

    // Plot Depth Profile Line & Area
    ctx.beginPath();
    let hasStarted = false;

    // Filter valid points
    const validPoints: { depth: number; val: number; x: number; y: number }[] = [];

    for (let i = 0; i < depths.length; i++) {
      const d = depths[i];
      const v = values[i];
      if (v === null || v === undefined || isNaN(v)) continue;

      const x = valToX(v);
      const y = depthToY(d);
      validPoints.push({ depth: d, val: v, x, y });

      if (!hasStarted) {
        ctx.moveTo(x, y);
        hasStarted = true;
      } else {
        ctx.lineTo(x, y);
      }
    }

    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw point markers
    validPoints.forEach((pt) => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 3, 0, 2 * Math.PI);
      ctx.fillStyle = '#38bdf8';
      ctx.fill();
    });

  }, [profileData]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!profileData || !profileData.depths?.length) return;
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
      const minDepth = Math.min(...profileData.depths);
      const maxDepth = Math.max(...profileData.depths);
      const depthRange = (maxDepth - minDepth) || 1;

      const normY = (mouseY - padTop) / plotH;
      const targetDepth = minDepth + normY * depthRange;

      // Find nearest depth point
      let nearestIdx = 0;
      let minDiff = Infinity;
      profileData.depths.forEach((d: number, idx: number) => {
        const diff = Math.abs(d - targetDepth);
        if (diff < minDiff && profileData.values[idx] !== null) {
          minDiff = diff;
          nearestIdx = idx;
        }
      });

      const matchedVal = profileData.values[nearestIdx];
      if (matchedVal !== null) {
        setHoveredPoint({
          depth: profileData.depths[nearestIdx],
          val: matchedVal,
          screenX: mouseX,
          screenY: mouseY,
        });
      }
    } else {
      setHoveredPoint(null);
    }
  };

  if (!profileData) {
    return (
      <div style={{ padding: '1rem', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <EmptyState
          icon="info"
          title="Select a point on the map to explore the water column"
          description="Click any coordinate on the spatial map to view vertical temperature, salinity, or parameter sounding with depth."
        />
      </div>
    );
  }

  const rawVar = profileData.variable || profileData.variable_name;
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
          <strong style={{ color: 'var(--accent-cyan)' }}>DEPTH PROFILE</strong>: {varDisplay.label} ({rawVar}) {profileData.units ? `[${profileData.units}]` : ''}
        </div>
        <div>
          LAT: {(profileData.lat ?? profileData.actual_latitude ?? 0).toFixed(2)}° | LON: {(profileData.lon ?? profileData.actual_longitude ?? 0).toFixed(2)}°
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
          <div>Depth: <strong style={{ color: 'var(--accent-cyan)' }}>{hoveredPoint.depth} {profileData.depth_units || 'm'}</strong></div>
          <div>Value: <strong style={{ color: 'var(--accent-emerald)' }}>{hoveredPoint.val.toFixed(3)} {profileData.units}</strong></div>
        </div>
      )}
    </div>
  );
};
