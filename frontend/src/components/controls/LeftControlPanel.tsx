import React from 'react';
import { 
  Layers, 
  Clock, 
  Anchor, 
  Palette, 
  Navigation, 
  MapPin, 
  Activity,
  GitCompare,
  Route,
  Filter
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';
import { type ColormapName, COLORMAP_NAMES } from '../../utils/colormaps';

export const LeftControlPanel: React.FC = () => {
  const {
    datasets,
    datasetId,
    setDatasetId,
    metadata,
    variables,
    primaryVariable,
    setPrimaryVariable,
    secondaryVariable,
    setSecondaryVariable,
    timeIndex,
    setTimeIndex,
    depthIndex,
    setDepthIndex,
    probeLat,
    probeLon,
    setProbeCoords,
    transectCoords,
    setTransectCoords,
    analysisMode,
    colormap,
    setColormap,
    showVectors,
    setShowVectors,
    speedThreshold,
    setSpeedThreshold,
  } = useAnalysis();

  const timeStepsCount = metadata?.temporal_coverage?.time_steps_count || 
                         metadata?.temporal_extent?.total_timesteps || 1;
  const depthsCount = metadata?.depth_levels?.length || 
                      metadata?.depth_extent?.depth_levels_count || 1;

  const hasVectorData = variables.some((v) => ['u', 'uo', 'water_u'].includes((v.name || v.variable_name || '').toLowerCase())) &&
                        variables.some((v) => ['v', 'vo', 'water_v'].includes((v.name || v.variable_name || '').toLowerCase()));

  return (
    <aside style={{
      width: '320px',
      minWidth: '280px',
      backgroundColor: 'var(--bg-deep)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      gap: '1.25rem',
      padding: '1.25rem 1rem',
      overflowY: 'auto',
      height: '100%',
      boxSizing: 'border-box',
    }}>
      {/* 1. Dataset Selection */}
      <div className="control-group">
        <label className="control-label" style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <Layers size={14} className="text-accent-cyan" />
          SCIENTIFIC DATASET
        </label>
        <select
          value={datasetId || ''}
          onChange={(e) => setDatasetId(e.target.value)}
          className="select-input"
          style={{
            width: '100%',
            padding: '0.5rem 0.625rem',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)',
            fontSize: '0.8125rem',
            fontFamily: 'var(--font-sans)',
          }}
        >
          {datasets.length === 0 ? (
            <option value="" disabled>No registered datasets</option>
          ) : (
            datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.source || 'Standard'})
              </option>
            ))
          )}
        </select>
      </div>

      {/* 2. Primary Variable Selection */}
      <div className="control-group">
        <label className="control-label" style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <Activity size={14} className="text-accent-cyan" />
          {analysisMode === 'compare' ? 'PRIMARY VARIABLE (X)' : 'ACTIVE VARIABLE'}
        </label>
        {variables.length === 0 ? (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', padding: '0.25rem 0' }}>
            No variables found for this dataset.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.375rem' }}>
            {variables.map((v) => {
              const varName = v.name || v.variable_name || '';
              const isSelected = primaryVariable === varName;
              return (
                <button
                  key={varName}
                  onClick={() => setPrimaryVariable(varName)}
                  style={{
                    padding: '0.4rem 0.5rem',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.75rem',
                    fontFamily: 'var(--font-mono)',
                    textAlign: 'left',
                    cursor: 'pointer',
                    backgroundColor: isSelected ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-surface)',
                    border: isSelected ? '1px solid var(--border-focus)' : '1px solid var(--border-subtle)',
                    color: isSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    {varName}
                    {v.is_derived && (
                      <span style={{ fontSize: '0.5625rem', color: 'var(--accent-amber)', backgroundColor: 'rgba(245, 158, 11, 0.15)', padding: '0.05rem 0.25rem', borderRadius: '2px' }}>
                        DERIVED
                      </span>
                    )}
                  </span>
                  <span style={{ fontSize: '0.625rem', color: isSelected ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                    {v.units || 'unitless'}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* 3. Secondary Variable Selection (Compare Mode) */}
      {analysisMode === 'compare' && (
        <div className="control-group" style={{
          padding: '0.75rem',
          backgroundColor: 'rgba(56, 189, 248, 0.05)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-focus)',
        }}>
          <label className="control-label" style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--accent-cyan)' }}>
            <GitCompare size={14} />
            SECONDARY VARIABLE (Y)
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.375rem', marginTop: '0.5rem' }}>
            {variables.map((v) => {
              const varName = v.name || v.variable_name || '';
              const isSelected = secondaryVariable === varName;
              return (
                <button
                  key={`sec-${varName}`}
                  onClick={() => setSecondaryVariable(varName)}
                  style={{
                    padding: '0.4rem 0.5rem',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.75rem',
                    fontFamily: 'var(--font-mono)',
                    textAlign: 'left',
                    cursor: 'pointer',
                    backgroundColor: isSelected ? 'rgba(16, 185, 129, 0.2)' : 'var(--bg-surface)',
                    border: isSelected ? '1px solid var(--accent-emerald)' : '1px solid var(--border-subtle)',
                    color: isSelected ? 'var(--accent-emerald)' : 'var(--text-secondary)',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <span style={{ fontWeight: 600 }}>{varName}</span>
                  <span style={{ fontSize: '0.625rem', color: isSelected ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                    {v.units || 'unitless'}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Transect Endpoints Controls (Transect Mode) */}
      {analysisMode === 'transect' && (
        <div className="control-group" style={{
          padding: '0.75rem',
          backgroundColor: 'rgba(56, 189, 248, 0.05)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-focus)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.625rem',
        }}>
          <label className="control-label" style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--accent-cyan)' }}>
            <Route size={14} />
            TRANSECT PATH (GREAT CIRCLE)
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--accent-cyan)' }}>PT A LAT (°N)</span>
              <input
                type="number"
                step="0.5"
                value={transectCoords.lat1}
                onChange={(e) => setTransectCoords((p) => ({ ...p, lat1: parseFloat(e.target.value) || 0 }))}
                style={{ width: '100%', padding: '0.35rem', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}
              />
            </div>
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--accent-cyan)' }}>PT A LON (°E)</span>
              <input
                type="number"
                step="0.5"
                value={transectCoords.lon1}
                onChange={(e) => setTransectCoords((p) => ({ ...p, lon1: parseFloat(e.target.value) || 0 }))}
                style={{ width: '100%', padding: '0.35rem', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}
              />
            </div>
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--accent-emerald)' }}>PT B LAT (°N)</span>
              <input
                type="number"
                step="0.5"
                value={transectCoords.lat2}
                onChange={(e) => setTransectCoords((p) => ({ ...p, lat2: parseFloat(e.target.value) || 0 }))}
                style={{ width: '100%', padding: '0.35rem', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}
              />
            </div>
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--accent-emerald)' }}>PT B LON (°E)</span>
              <input
                type="number"
                step="0.5"
                value={transectCoords.lon2}
                onChange={(e) => setTransectCoords((p) => ({ ...p, lon2: parseFloat(e.target.value) || 0 }))}
                style={{ width: '100%', padding: '0.35rem', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}
              />
            </div>
          </div>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              <span>Interpolation Steps</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{transectCoords.numPoints} samples</span>
            </div>
            <input
              type="range"
              min={10}
              max={100}
              value={transectCoords.numPoints}
              onChange={(e) => setTransectCoords((p) => ({ ...p, numPoints: parseInt(e.target.value) }))}
              style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
            />
          </div>
        </div>
      )}

      {/* 5. Temporal & Vertical Slicing */}
      <div className="control-group" style={{
        padding: '0.875rem',
        backgroundColor: 'rgba(15, 23, 42, 0.6)',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.875rem',
      }}>
        {/* Time Step */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.375rem', fontSize: '0.75rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--text-secondary)' }}>
              <Clock size={12} /> Time Step
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
              {timeStepsCount > 0 ? `${timeIndex + 1} / ${timeStepsCount}` : 'Static'}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={Math.max(0, timeStepsCount - 1)}
            value={timeIndex}
            onChange={(e) => setTimeIndex(Number(e.target.value))}
            disabled={timeStepsCount <= 1}
            style={{ width: '100%', accentColor: 'var(--accent-cyan)', cursor: timeStepsCount > 1 ? 'pointer' : 'not-allowed' }}
          />
        </div>

        {/* Depth Level */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.375rem', fontSize: '0.75rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--text-secondary)' }}>
              <Anchor size={12} /> Depth Level
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
              {depthsCount > 0 ? `Level ${depthIndex + 1} / ${depthsCount}` : 'Surface (0m)'}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={Math.max(0, depthsCount - 1)}
            value={depthIndex}
            onChange={(e) => setDepthIndex(Number(e.target.value))}
            disabled={depthsCount <= 1}
            style={{ width: '100%', accentColor: 'var(--accent-cyan)', cursor: depthsCount > 1 ? 'pointer' : 'not-allowed' }}
          />
        </div>
      </div>

      {/* 6. Scientific Colormap */}
      <div className="control-group">
        <label className="control-label" style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <Palette size={14} className="text-accent-cyan" />
          SCIENTIFIC COLORMAP
        </label>
        <select
          value={colormap}
          onChange={(e) => setColormap(e.target.value as ColormapName)}
          className="select-input"
          style={{
            width: '100%',
            padding: '0.4rem 0.625rem',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
          }}
        >
          {COLORMAP_NAMES.map((cm) => (
            <option key={cm} value={cm}>
              {cm.toUpperCase()}
            </option>
          ))}
        </select>
      </div>

      {/* 7. Current Vectors & Velocity Filter */}
      <div className="control-group" style={{
        padding: '0.75rem',
        backgroundColor: 'rgba(15, 23, 42, 0.4)',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--text-secondary)' }}>
            <Navigation size={13} className={hasVectorData ? 'text-accent-cyan' : 'text-text-muted'} />
            Current Vectors (U/V)
          </span>
          <input
            type="checkbox"
            checked={showVectors || analysisMode === 'currents'}
            onChange={(e) => setShowVectors(e.target.checked)}
            disabled={!hasVectorData}
            style={{ cursor: hasVectorData ? 'pointer' : 'not-allowed', accentColor: 'var(--accent-cyan)' }}
          />
        </div>
        
        {hasVectorData && (showVectors || analysisMode === 'currents') && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Filter size={11} /> Speed Cutoff Filter
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                {speedThreshold.toFixed(2)} m/s
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={3.0}
              step={0.05}
              value={speedThreshold}
              onChange={(e) => setSpeedThreshold(parseFloat(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
            />
          </div>
        )}

        {!hasVectorData && (
          <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>
            Dataset lacks U/V velocity components.
          </div>
        )}
      </div>

      {/* 8. Station Coordinates Probe */}
      <div className="control-group">
        <label className="control-label" style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <MapPin size={14} className="text-accent-cyan" />
          STATION PROBE COORDINATES
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>LAT (°N/S)</span>
            <input
              type="number"
              step="0.1"
              value={probeLat !== null ? probeLat : ''}
              onChange={(e) => setProbeCoords(parseFloat(e.target.value) || 0, probeLon ?? 0)}
              placeholder="0.0"
              style={{
                width: '100%',
                padding: '0.375rem 0.5rem',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                boxSizing: 'border-box',
              }}
            />
          </div>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>LON (°E/W)</span>
            <input
              type="number"
              step="0.1"
              value={probeLon !== null ? probeLon : ''}
              onChange={(e) => setProbeCoords(probeLat ?? 0, parseFloat(e.target.value) || 0)}
              placeholder="0.0"
              style={{
                width: '100%',
                padding: '0.375rem 0.5rem',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                boxSizing: 'border-box',
              }}
            />
          </div>
        </div>
      </div>
    </aside>
  );
};

