import React, { useRef, useEffect, useState, useCallback } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Spline, 
  BoxSelect,
  HelpCircle,
  X
} from 'lucide-react';
import type { 
  GridDeliveryResponse, 
  CurrentsDeliveryResponse, 
  CurrentVectorItem, 
  TransectCoords, 
  AnalysisMode,
  ScientificAnnotation
} from '../../types';
import { useAnalysis } from '../../context/AnalysisContext';
import { type ColormapName, getColorRgba } from '../../utils/colormaps';
import { getVariableDisplay } from '../../utils/variableNames';
import { ColormapLegend } from './ColormapLegend';

interface ScientificMapCanvasProps {
  gridData?: GridDeliveryResponse | null;
  secondaryGridData?: GridDeliveryResponse | null;
  vectorData?: CurrentsDeliveryResponse | null;
  colormap?: ColormapName;
  onColormapChange?: (name: ColormapName) => void;
  selectedVariable?: string;
  secondaryVariable?: string | null;
  units?: string;
  analysisMode?: AnalysisMode;
  onCoordinateSelect?: (lat: number, lon: number) => void;
  selectedLat?: number | null;
  selectedLon?: number | null;
  showVectors?: boolean;
  speedThreshold?: number;
  transectCoords?: TransectCoords;
  onUpdateTransectCoords?: (coords: Partial<TransectCoords>) => void;
}

// Top-level canvas rendering helpers
const drawCoordinateGrid = (ctx: CanvasRenderingContext2D, w: number, h: number) => {
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 4]);
  for (let x = 60; x < w; x += 60) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let y = 60; y < h; y += 60) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }
  ctx.setLineDash([]);
};

const drawAxes = (
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  padLeft: number,
  padRight: number,
  padTop: number,
  padBottom: number,
  minLat: number,
  maxLat: number,
  minLon: number,
  maxLon: number
) => {
  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  ctx.strokeStyle = '#2a3a5c';
  ctx.lineWidth = 1;
  ctx.strokeRect(padLeft, padTop, plotW, plotH);

  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px "JetBrains Mono", monospace';

  // Latitude ticks
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  const latTicks = 6;
  for (let i = 0; i <= latTicks; i++) {
    const frac = i / latTicks;
    const latVal = minLat + frac * (maxLat - minLat);
    const y = padTop + (1 - frac) * plotH;

    ctx.beginPath();
    ctx.moveTo(padLeft - 5, y);
    ctx.lineTo(padLeft, y);
    ctx.stroke();

    const suffix = latVal >= 0 ? '°N' : '°S';
    ctx.fillText(`${Math.abs(latVal).toFixed(1)}${suffix}`, padLeft - 8, y);
  }

  // Longitude ticks
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  const lonTicks = 8;
  for (let i = 0; i <= lonTicks; i++) {
    const frac = i / lonTicks;
    const lonVal = minLon + frac * (maxLon - minLon);
    const x = padLeft + frac * plotW;

    ctx.beginPath();
    ctx.moveTo(x, padTop + plotH);
    ctx.lineTo(x, padTop + plotH + 5);
    ctx.stroke();

    const suffix = lonVal >= 0 ? '°E' : '°W';
    ctx.fillText(`${Math.abs(lonVal).toFixed(1)}${suffix}`, x, padTop + plotH + 8);
  }
};

export const ScientificMapCanvas: React.FC<ScientificMapCanvasProps> = ({
  gridData: propGrid,
  secondaryGridData: propSecGrid,
  vectorData: propVectors,
  colormap: propColormap,
  onColormapChange: propColormapChange,
  selectedVariable: propVar,
  secondaryVariable: propSecVar,
  units: propUnits,
  analysisMode: propMode,
  onCoordinateSelect: propCoordSelect,
  selectedLat: propLat,
  selectedLon: propLon,
  showVectors: propShowVectors,
  speedThreshold: propSpeedThresh,
  transectCoords: propTransect,
  onUpdateTransectCoords: propUpdateTransect,
}) => {
  const context = useAnalysis();

  const gridData = propGrid !== undefined ? propGrid : context.gridData;
  const secondaryGridData = propSecGrid !== undefined ? propSecGrid : context.secondaryGridData;
  const vectorData = propVectors !== undefined ? propVectors : context.vectorData;
  const colormap = propColormap ?? context.colormap;
  const onColormapChange = propColormapChange ?? context.setColormap;
  const selectedVariable = propVar ?? context.primaryVariable ?? '—';
  const secondaryVariable = propSecVar ?? context.secondaryVariable;
  const units = propUnits ?? context.statistics?.units ?? '';
  const analysisMode = propMode ?? context.analysisMode;
  const onCoordinateSelect = propCoordSelect ?? context.setProbeCoords;
  const selectedLat = propLat !== undefined ? propLat : context.probeLat;
  const selectedLon = propLon !== undefined ? propLon : context.probeLon;
  const showVectors = propShowVectors !== undefined ? propShowVectors : context.showVectors;
  const speedThreshold = propSpeedThresh !== undefined ? propSpeedThresh : context.speedThreshold;
  const transectCoords = propTransect ?? context.transectCoords;
  const onUpdateTransectCoords = propUpdateTransect ?? ((coords) => context.setTransectCoords((p) => ({ ...p, ...coords })));
  const annotations = context.annotations || [];
  const displayScale = context.displayScale || { mode: 'auto' };
  const regionBounds = context.regionBounds;
  const setRegionBounds = context.setRegionBounds;

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Viewport transform state (Zoom & Pan)
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Box Selection Mode
  const [isBoxSelecting, setIsBoxSelecting] = useState<boolean>(false);
  const [boxStart, setBoxStart] = useState<{ x: number; y: number; lat: number; lon: number } | null>(null);
  const [boxCurrent, setBoxCurrent] = useState<{ x: number; y: number; lat: number; lon: number } | null>(null);

  // Transect placement state
  const [transectClickStep, setTransectClickStep] = useState<0 | 1>(0);

  // Dynamic "What am I seeing?" explanation toggle
  const [showExplanation, setShowExplanation] = useState<boolean>(true);

  // Hover state
  const [hoverInfo, setHoverInfo] = useState<{
    lat: number;
    lon: number;
    val: number | null;
    secVal?: number | null;
    screenX: number;
    screenY: number;
  } | null>(null);

  const resetView = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  // Main Canvas Render Pipeline
  useEffect(() => {
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
    ctx.fillStyle = '#060911';
    ctx.fillRect(0, 0, width, height);

    // If no grid data, render coordinate radar grid
    if (!gridData || !gridData.latitudes?.length || !gridData.longitudes?.length) {
      drawCoordinateGrid(ctx, width, height);
      return;
    }

    const { latitudes, longitudes, values } = gridData;
    let minVal = gridData.min_value ?? 0;
    let maxVal = gridData.max_value ?? 1;

    // Apply Display Scale Controls (Manual or Percentile without altering source data)
    if (displayScale.mode === 'manual') {
      if (displayScale.manualMin !== undefined) minVal = displayScale.manualMin;
      if (displayScale.manualMax !== undefined) maxVal = displayScale.manualMax;
    }

    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    const minLon = Math.min(...longitudes);
    const maxLon = Math.max(...longitudes);

    // Padding for axes
    const padLeft = 50;
    const padBottom = 30;
    const padTop = 20;
    const padRight = 20;

    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    ctx.save();
    ctx.beginPath();
    ctx.rect(padLeft, padTop, plotW, plotH);
    ctx.clip();

    const lonToX = (lon: number) => {
      const norm = (lon - minLon) / (maxLon - minLon || 1);
      const baseX = padLeft + norm * plotW;
      const centerX = padLeft + plotW / 2;
      return (baseX - centerX) * zoom + centerX + pan.x;
    };

    const latToY = (lat: number) => {
      const norm = (lat - minLat) / (maxLat - minLat || 1);
      const baseY = padTop + (1 - norm) * plotH;
      const centerY = padTop + plotH / 2;
      return (baseY - centerY) * zoom + centerY + pan.y;
    };

    // Render Heatmap Matrix
    const rows = latitudes.length;
    const cols = longitudes.length;

    if (rows > 0 && cols > 0 && values && values.length > 0) {
      const offscreen = document.createElement('canvas');
      offscreen.width = cols;
      offscreen.height = rows;
      const offCtx = offscreen.getContext('2d');

      if (offCtx) {
        const imgData = offCtx.createImageData(cols, rows);
        const data = imgData.data;

        for (let r = 0; r < rows; r++) {
          const rowVals = values[r];
          if (!rowVals) continue;

          for (let c = 0; c < cols; c++) {
            const v = rowVals[c];
            const idx = (r * cols + c) * 4;

            if (v === null || v === undefined || isNaN(v) || !isFinite(v)) {
              data[idx] = 10;
              data[idx + 1] = 15;
              data[idx + 2] = 29;
              data[idx + 3] = 255;
            } else {
              const norm = Math.max(0, Math.min(1, (v - minVal) / (maxVal - minVal || 1)));
              const [red, green, blue] = getColorRgba(norm, colormap);
              data[idx] = red;
              data[idx + 1] = green;
              data[idx + 2] = blue;
              data[idx + 3] = 255;
            }
          }
        }

        offCtx.putImageData(imgData, 0, 0);

        const x0 = lonToX(minLon);
        const x1 = lonToX(maxLon);
        const y0 = latToY(maxLat);
        const y1 = latToY(minLat);

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(offscreen, x0, y0, x1 - x0, y1 - y0);
      }
    }

    // Render Currents Vector Overlay
    if (showVectors && vectorData && vectorData.vectors && vectorData.vectors.length > 0) {
      ctx.lineWidth = 1.5;

      vectorData.vectors.forEach((vec: CurrentVectorItem) => {
        const speed = vec.speed ?? Math.sqrt(vec.u * vec.u + vec.v * vec.v);
        if (speed < speedThreshold) return;

        const vx = lonToX(vec.lon ?? vec.longitude ?? 0);
        const vy = latToY(vec.lat ?? vec.latitude ?? 0);

        if (vx < padLeft - 20 || vx > padLeft + plotW + 20 || vy < padTop - 20 || vy > padTop + plotH + 20) {
          return;
        }

        const angle = Math.atan2(-vec.v, vec.u);
        const arrowLen = Math.min(24, Math.max(6, speed * 15 * zoom));

        const endX = vx + arrowLen * Math.cos(angle);
        const endY = vy + arrowLen * Math.sin(angle);

        ctx.strokeStyle = 'rgba(248, 250, 252, 0.85)';
        ctx.fillStyle = 'rgba(248, 250, 252, 0.85)';

        ctx.beginPath();
        ctx.moveTo(vx, vy);
        ctx.lineTo(endX, endY);
        ctx.stroke();

        const headLen = Math.min(6, arrowLen * 0.35);
        ctx.beginPath();
        ctx.moveTo(endX, endY);
        ctx.lineTo(
          endX - headLen * Math.cos(angle - Math.PI / 6),
          endY - headLen * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          endX - headLen * Math.cos(angle + Math.PI / 6),
          endY - headLen * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fill();
      });
    }

    // Render Regional Bounding Box if set
    if (regionBounds) {
      const rx1 = lonToX(regionBounds.minLon);
      const rx2 = lonToX(regionBounds.maxLon);
      const ry1 = latToY(regionBounds.maxLat);
      const ry2 = latToY(regionBounds.minLat);

      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.fillStyle = 'rgba(56, 189, 248, 0.15)';
      ctx.fillRect(Math.min(rx1, rx2), Math.min(ry1, ry2), Math.abs(rx2 - rx1), Math.abs(ry2 - ry1));
      ctx.strokeRect(Math.min(rx1, rx2), Math.min(ry1, ry2), Math.abs(rx2 - rx1), Math.abs(ry2 - ry1));
      ctx.setLineDash([]);
    }

    // Render Active Box Selection Drag Rectangle
    if (isBoxSelecting && boxStart && boxCurrent) {
      const bx = Math.min(boxStart.x, boxCurrent.x);
      const by = Math.min(boxStart.y, boxCurrent.y);
      const bw = Math.abs(boxCurrent.x - boxStart.x);
      const bh = Math.abs(boxCurrent.y - boxStart.y);

      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2;
      ctx.fillStyle = 'rgba(16, 185, 129, 0.2)';
      ctx.fillRect(bx, by, bw, bh);
      ctx.strokeRect(bx, by, bw, bh);
    }

    // Render Transect Line & Markers
    if (analysisMode === 'transect' && transectCoords) {
      const x1 = lonToX(transectCoords.lon1);
      const y1 = latToY(transectCoords.lat1);
      const x2 = lonToX(transectCoords.lon2);
      const y2 = latToY(transectCoords.lat2);

      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2.5;
      ctx.setLineDash([6, 3]);

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#38bdf8';
      ctx.beginPath();
      ctx.arc(x1, y1, 6, 0, 2 * Math.PI);
      ctx.fill();

      ctx.fillStyle = '#10b981';
      ctx.beginPath();
      ctx.arc(x2, y2, 6, 0, 2 * Math.PI);
      ctx.fill();

      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 11px "JetBrains Mono", monospace';
      ctx.fillText('A', x1 + 8, y1 - 8);
      ctx.fillText('B', x2 + 8, y2 - 8);
    }

    // Render Scientific Annotation Markers (Pins)
    annotations.forEach((ann: ScientificAnnotation) => {
      const ax = lonToX(ann.longitude);
      const ay = latToY(ann.latitude);

      if (ax >= padLeft && ax <= padLeft + plotW && ay >= padTop && ay <= padTop + plotH) {
        ctx.fillStyle = 'rgba(245, 158, 11, 0.85)';
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;

        ctx.beginPath();
        ctx.arc(ax, ay, 5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
      }
    });

    // Selected Station Crosshair Marker
    if (selectedLat !== null && selectedLat !== undefined && selectedLon !== null && selectedLon !== undefined) {
      const sx = lonToX(selectedLon);
      const sy = latToY(selectedLat);

      if (sx >= padLeft && sx <= padLeft + plotW && sy >= padTop && sy <= padTop + plotH) {
        ctx.strokeStyle = '#f43f5e';
        ctx.fillStyle = 'rgba(244, 63, 94, 0.3)';
        ctx.lineWidth = 2;

        ctx.beginPath();
        ctx.arc(sx, sy, 8, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(sx - 12, sy);
        ctx.lineTo(sx + 12, sy);
        ctx.moveTo(sx, sy - 12);
        ctx.lineTo(sx, sy + 12);
        ctx.stroke();
      }
    }

    ctx.restore();

    // Axes
    drawAxes(ctx, width, height, padLeft, padRight, padTop, padBottom, minLat, maxLat, minLon, maxLon);

  }, [
    gridData,
    secondaryGridData,
    vectorData,
    colormap,
    zoom,
    pan,
    selectedLat,
    selectedLon,
    showVectors,
    speedThreshold,
    analysisMode,
    transectCoords,
    annotations,
    displayScale,
    regionBounds,
    isBoxSelecting,
    boxStart,
    boxCurrent,
  ]);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (isBoxSelecting && hoverInfo) {
      setBoxStart({ x: mouseX, y: mouseY, lat: hoverInfo.lat, lon: hoverInfo.lon });
      setBoxCurrent({ x: mouseX, y: mouseY, lat: hoverInfo.lat, lon: hoverInfo.lon });
    } else {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }

    if (!gridData || !gridData.latitudes?.length || !gridData.longitudes?.length) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const padLeft = 50;
    const padBottom = 30;
    const padTop = 20;
    const padRight = 20;
    const plotW = rect.width - padLeft - padRight;
    const plotH = rect.height - padTop - padBottom;

    if (mouseX >= padLeft && mouseX <= padLeft + plotW && mouseY >= padTop && mouseY <= padTop + plotH) {
      const minLat = Math.min(...gridData.latitudes);
      const maxLat = Math.max(...gridData.latitudes);
      const minLon = Math.min(...gridData.longitudes);
      const maxLon = Math.max(...gridData.longitudes);

      const centerX = padLeft + plotW / 2;
      const centerY = padTop + plotH / 2;

      const unzoomedX = (mouseX - centerX - pan.x) / zoom + centerX;
      const unzoomedY = (mouseY - centerY - pan.y) / zoom + centerY;

      const normX = Math.max(0, Math.min(1, (unzoomedX - padLeft) / plotW));
      const normY = Math.max(0, Math.min(1, 1 - (unzoomedY - padTop) / plotH));

      const hoveredLon = minLon + normX * (maxLon - minLon);
      const hoveredLat = minLat + normY * (maxLat - minLat);

      const latIdx = Math.round(normY * (gridData.latitudes.length - 1));
      const lonIdx = Math.round(normX * (gridData.longitudes.length - 1));
      const val = gridData.values[latIdx]?.[lonIdx] ?? null;
      const secVal = secondaryGridData?.values?.[latIdx]?.[lonIdx] ?? null;

      setHoverInfo({
        lat: hoveredLat,
        lon: hoveredLon,
        val,
        secVal,
        screenX: mouseX,
        screenY: mouseY,
      });

      if (isBoxSelecting && boxStart) {
        setBoxCurrent({ x: mouseX, y: mouseY, lat: hoveredLat, lon: hoveredLon });
      }
    } else {
      setHoverInfo(null);
    }
  };

  const handleMouseUp = () => {
    if (isBoxSelecting && boxStart && boxCurrent) {
      const minLat = Math.min(boxStart.lat, boxCurrent.lat);
      const maxLat = Math.max(boxStart.lat, boxCurrent.lat);
      const minLon = Math.min(boxStart.lon, boxCurrent.lon);
      const maxLon = Math.max(boxStart.lon, boxCurrent.lon);

      if (Math.abs(maxLat - minLat) > 0.1 && Math.abs(maxLon - minLon) > 0.1) {
        setRegionBounds({ minLat, maxLat, minLon, maxLon });
      }

      setBoxStart(null);
      setBoxCurrent(null);
      setIsBoxSelecting(false);
    }
    setIsDragging(false);
  };

  const handleClick = () => {
    if (isBoxSelecting || !hoverInfo) return;

    // In Transect mode: alternate setting Point A and Point B
    if (analysisMode === 'transect') {
      if (transectClickStep === 0) {
        onUpdateTransectCoords({ lat1: hoverInfo.lat, lon1: hoverInfo.lon });
        setTransectClickStep(1);
      } else {
        onUpdateTransectCoords({ lat2: hoverInfo.lat, lon2: hoverInfo.lon });
        setTransectClickStep(0);
      }
      return;
    }

    if (onCoordinateSelect) {
      onCoordinateSelect(hoverInfo.lat, hoverInfo.lon);
    }
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
    setZoom((prev) => Math.max(0.5, Math.min(10, prev * zoomFactor)));
  };

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        minHeight: '450px',
        backgroundColor: 'var(--bg-abyss)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-default)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Canvas */}
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          cursor: isBoxSelecting ? 'crosshair' : isDragging ? 'grabbing' : analysisMode === 'transect' ? 'crosshair' : 'crosshair',
          display: 'block',
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => {
          setIsDragging(false);
          setHoverInfo(null);
        }}
        onClick={handleClick}
        onWheel={handleWheel}
      />

      {/* Floating Toolbar Controls */}
      <div style={{
        position: 'absolute',
        top: '12px',
        right: '12px',
        display: 'flex',
        alignItems: 'center',
        gap: '0.375rem',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(8px)',
        padding: '0.25rem 0.5rem',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-default)',
        zIndex: 10,
      }}>
        {/* Box Select Toggle */}
        <button
          onClick={() => setIsBoxSelecting((prev) => !prev)}
          title={isBoxSelecting ? 'Cancel Box Selection' : 'Select Spatial Bounding Box'}
          style={{
            background: isBoxSelecting ? 'rgba(16, 185, 129, 0.25)' : 'none',
            border: isBoxSelecting ? '1px solid var(--accent-emerald)' : 'none',
            color: isBoxSelecting ? 'var(--accent-emerald)' : 'var(--text-secondary)',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <BoxSelect size={16} />
        </button>

        <button
          onClick={() => setZoom((z) => Math.min(10, z * 1.25))}
          title="Zoom In"
          style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px' }}
        >
          <ZoomIn size={16} />
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(0.5, z * 0.8))}
          title="Zoom Out"
          style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px' }}
        >
          <ZoomOut size={16} />
        </button>
        <button
          onClick={resetView}
          title="Reset View Transform"
          style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px' }}
        >
          <RotateCcw size={16} />
        </button>
      </div>

      {/* Dynamic "What am I seeing?" Explanation Banner */}
      {analysisMode === 'explore' && gridData && showExplanation && (
        <div style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          maxWidth: '380px',
          backgroundColor: 'rgba(8, 14, 30, 0.92)',
          backdropFilter: 'blur(10px)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.625rem 0.85rem',
          zIndex: 10,
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
          fontSize: '0.75rem',
          lineHeight: 1.45,
          color: 'var(--text-secondary)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.25rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              color: 'var(--accent-cyan)',
              fontWeight: 600,
              fontFamily: 'var(--font-mono)',
              fontSize: '0.6875rem',
              letterSpacing: '0.04em',
            }}>
              <HelpCircle size={13} />
              WHAT AM I SEEING?
            </span>
            <button
              onClick={() => setShowExplanation(false)}
              title="Dismiss note"
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '2px',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <X size={13} />
            </button>
          </div>
          <div>
            This map shows <strong style={{ color: 'var(--text-primary)' }}>{getVariableDisplay(selectedVariable).label}</strong> ({selectedVariable}) across <strong style={{ color: 'var(--text-primary)' }}>{context.metadata?.name || 'the regional grid'}</strong>. Colors represent values{units ? ` in ${units}` : ''}.
          </div>
        </div>
      )}

      {analysisMode === 'explore' && !showExplanation && (
        <button
          onClick={() => setShowExplanation(true)}
          title="Explain current map view"
          style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            backgroundColor: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(8px)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.3rem 0.6rem',
            zIndex: 10,
            color: 'var(--accent-cyan)',
            fontSize: '0.6875rem',
            fontFamily: 'var(--font-mono)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
          }}
        >
          <HelpCircle size={13} />
          <span>What am I seeing?</span>
        </button>
      )}

      {/* Mode Specific Notice Banner */}
      {analysisMode === 'transect' && (
        <div style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          backgroundColor: 'rgba(245, 158, 11, 0.9)',
          color: '#000',
          padding: '0.25rem 0.625rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
          fontWeight: 600,
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
        }}>
          <Spline size={13} />
          {transectClickStep === 0 ? 'Click map to set Point A' : 'Click map to set Point B'}
        </div>
      )}

      {isBoxSelecting && (
        <div style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          backgroundColor: 'rgba(16, 185, 129, 0.9)',
          color: '#000',
          padding: '0.25rem 0.625rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
          fontWeight: 600,
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
        }}>
          <BoxSelect size={13} />
          Click and drag on map to select bounding region
        </div>
      )}

      {/* Interactive Tooltip & Coordinate HUD */}
      {hoverInfo && (
        <div style={{
          position: 'absolute',
          bottom: '12px',
          left: '12px',
          backgroundColor: 'rgba(10, 15, 29, 0.9)',
          backdropFilter: 'blur(8px)',
          border: '1px solid var(--border-focus)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.5rem 0.75rem',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          color: 'var(--text-primary)',
          pointerEvents: 'none',
          zIndex: 10,
          display: 'flex',
          gap: '0.875rem',
          alignItems: 'center',
          boxShadow: 'var(--shadow-cyan)',
        }}>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>LAT: </span>
            <span style={{ color: 'var(--accent-cyan)' }}>{hoverInfo.lat.toFixed(3)}°</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>LON: </span>
            <span style={{ color: 'var(--accent-cyan)' }}>{hoverInfo.lon.toFixed(3)}°</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>{selectedVariable}: </span>
            <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>
              {hoverInfo.val !== null ? `${hoverInfo.val.toFixed(3)} ${units}` : 'NaN'}
            </span>
          </div>
          {hoverInfo.secVal !== null && hoverInfo.secVal !== undefined && (
            <div>
              <span style={{ color: 'var(--text-muted)' }}>{secondaryVariable}: </span>
              <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                {hoverInfo.secVal.toFixed(3)}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Colormap Legend */}
      {gridData && gridData.min_value !== undefined && gridData.max_value !== undefined && (
        <div style={{
          position: 'absolute',
          bottom: '12px',
          right: '12px',
          zIndex: 10,
        }}>
          <ColormapLegend
            variableName={selectedVariable}
            units={units}
            min={displayScale.manualMin ?? gridData.min_value}
            max={displayScale.manualMax ?? gridData.max_value}
            colormap={colormap}
            onColormapChange={onColormapChange}
          />
        </div>
      )}
    </div>
  );
};
