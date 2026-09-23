import React, { useState } from 'react';
import { 
  BarChart2, 
  Database, 
  Info,
  Cpu,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';
import { LoadingSkeleton } from '../common/LoadingSkeleton';
import { getVariableDisplay } from '../../utils/variableNames';

export const RightInfoPanel: React.FC = () => {
  const {
    metadata: dataset,
    variables,
    primaryVariable,
    statistics,
    summaryAnalysis,
    loading,
  } = useAnalysis();

  // Collapsible section state for progressive disclosure
  const [isVarInfoOpen, setIsVarInfoOpen] = useState<boolean>(true);
  const [isStatsOpen, setIsStatsOpen] = useState<boolean>(true);
  const [isSummaryOpen, setIsSummaryOpen] = useState<boolean>(false);
  const [isProvenanceOpen, setIsProvenanceOpen] = useState<boolean>(false);

  const activeVarInfo = variables.find((v) => (v.name || v.variable_name) === primaryVariable) || null;
  const activeVarMeta = getVariableDisplay(primaryVariable);

  const formatStat = (val?: number | null, precision = 3) => {
    if (val === undefined || val === null || isNaN(val) || !isFinite(val)) return '—';
    if (Math.abs(val) < 0.001 && val !== 0) return val.toExponential(2);
    if (Math.abs(val) >= 100000) return val.toExponential(2);
    return val.toFixed(precision);
  };

  const spatial = dataset?.spatial_coverage || dataset?.spatial_extent;
  const temporal = dataset?.temporal_coverage || dataset?.temporal_extent;

  return (
    <aside 
      aria-label="Scientific Metadata and Statistics"
      style={{
        width: '320px',
        minWidth: '280px',
        backgroundColor: 'var(--bg-deep)',
        borderLeft: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.875rem',
        padding: '1.25rem 1rem',
        overflowY: 'auto',
        height: '100%',
        boxSizing: 'border-box',
      }}
    >
      {/* 1. Variable Identity Card (Open by default) */}
      <div className="surface-card" style={{
        backgroundColor: 'var(--bg-surface)',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-default)',
        overflow: 'hidden',
      }}>
        <button
          onClick={() => setIsVarInfoOpen((prev) => !prev)}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.75rem 0.875rem',
            background: 'none',
            border: 'none',
            color: 'var(--accent-cyan)',
            cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.375rem',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}>
            <Info size={14} />
            VARIABLE METADATA
          </div>
          {isVarInfoOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>

        {isVarInfoOpen && (
          <div style={{ padding: '0 0.875rem 0.875rem' }}>
            {activeVarInfo ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Variable: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>
                      {activeVarMeta.label}
                    </strong>
                  </div>
                  {activeVarInfo.is_derived && (
                    <span style={{
                      fontSize: '0.625rem',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--accent-amber)',
                      backgroundColor: 'rgba(245, 158, 11, 0.15)',
                      padding: '0.1rem 0.35rem',
                      borderRadius: '2px',
                      fontWeight: 600,
                    }}>
                      DERIVED
                    </span>
                  )}
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Code: </span>
                  <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                    {activeVarInfo.name || activeVarInfo.variable_name}
                  </span>
                </div>
                {(activeVarInfo.standard_name || activeVarMeta.description) && (
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Description: </span>
                    <span style={{ color: 'var(--text-secondary)' }}>{activeVarInfo.standard_name || activeVarInfo.long_name || activeVarMeta.description}</span>
                  </div>
                )}
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Units: </span>
                  <span style={{ color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                    {activeVarInfo.units || 'unitless'}
                  </span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Dimensions: </span>
                  <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                    ({activeVarInfo.dimensions?.join(', ') || 'none'})
                  </span>
                </div>
                {activeVarInfo.shape && activeVarInfo.shape.length > 0 && (
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Shape: </span>
                    <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      [{activeVarInfo.shape.join(' × ')}]
                    </span>
                  </div>
                )}
                {(activeVarInfo.data_type || activeVarInfo.dtype) && (
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Data Type: </span>
                    <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      {activeVarInfo.data_type || activeVarInfo.dtype}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                No variable selected.
              </div>
            )}
          </div>
        )}
      </div>

      {/* 2. Scientific Distribution Statistics (Open by default) */}
      <div className="surface-card" style={{
        backgroundColor: 'var(--bg-surface)',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-default)',
        overflow: 'hidden',
      }}>
        <button
          onClick={() => setIsStatsOpen((prev) => !prev)}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.75rem 0.875rem',
            background: 'none',
            border: 'none',
            color: 'var(--accent-cyan)',
            cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.375rem',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}>
            <BarChart2 size={14} />
            SCIENTIFIC STATISTICS
          </div>
          {isStatsOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>

        {isStatsOpen && (
          <div style={{ padding: '0 0.875rem 0.875rem' }}>
            {loading.stats ? (
              <LoadingSkeleton type="stats" label="Computing statistics..." />
            ) : statistics ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
                  <div className="stat-box" style={{ padding: '0.5rem', backgroundColor: 'rgba(15, 23, 42, 0.6)', borderRadius: 'var(--radius-sm)' }}>
                    <span style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>MINIMUM</span>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                      {formatStat(statistics.min)}
                    </div>
                  </div>
                  <div className="stat-box" style={{ padding: '0.5rem', backgroundColor: 'rgba(15, 23, 42, 0.6)', borderRadius: 'var(--radius-sm)' }}>
                    <span style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>MAXIMUM</span>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                      {formatStat(statistics.max)}
                    </div>
                  </div>
                  <div className="stat-box" style={{ padding: '0.5rem', backgroundColor: 'rgba(15, 23, 42, 0.6)', borderRadius: 'var(--radius-sm)' }}>
                    <span style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>MEAN (μ)</span>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                      {formatStat(statistics.mean)}
                    </div>
                  </div>
                  <div className="stat-box" style={{ padding: '0.5rem', backgroundColor: 'rgba(15, 23, 42, 0.6)', borderRadius: 'var(--radius-sm)' }}>
                    <span style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>STD DEV (σ)</span>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                      {formatStat(statistics.std)}
                    </div>
                  </div>
                  <div className="stat-box" style={{ padding: '0.5rem', backgroundColor: 'rgba(15, 23, 42, 0.6)', borderRadius: 'var(--radius-sm)' }}>
                    <span style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>MEDIAN (P50)</span>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                      {formatStat(statistics.median)}
                    </div>
                  </div>
                  <div className="stat-box" style={{ padding: '0.5rem', backgroundColor: 'rgba(15, 23, 42, 0.6)', borderRadius: 'var(--radius-sm)' }}>
                    <span style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>P90</span>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                      {formatStat(statistics.p90)}
                    </div>
                  </div>
                </div>

                {/* Counts & Coverage */}
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.25rem',
                  fontSize: '0.6875rem',
                  fontFamily: 'var(--font-mono)',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '0.5rem',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Valid Cells:</span>
                    <span style={{ color: 'var(--accent-emerald)' }}>{statistics.valid_count?.toLocaleString() ?? '—'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Missing / NaN:</span>
                    <span style={{ color: statistics.missing_count ? 'var(--accent-rose)' : 'var(--text-muted)' }}>
                      {statistics.missing_count?.toLocaleString() ?? 0}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                No statistical summary available.
              </div>
            )}
          </div>
        )}
      </div>

      {/* 3. Dataset Analysis Summary (Progressive Disclosure - Collapsed by default) */}
      {summaryAnalysis && (
        <div className="surface-card" style={{
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-default)',
          overflow: 'hidden',
        }}>
          <button
            onClick={() => setIsSummaryOpen((prev) => !prev)}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.75rem 0.875rem',
              background: 'none',
              border: 'none',
              color: 'var(--accent-cyan)',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.375rem',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}>
              <Cpu size={14} />
              DATASET SUMMARY
            </div>
            {isSummaryOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>

          {isSummaryOpen && (
            <div style={{ padding: '0 0.875rem 0.875rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Registered Vars:</span>
                  <span style={{ color: 'var(--accent-cyan)' }}>{Object.keys(summaryAnalysis.key_variables || {}).length || variables.length}</span>
                </div>
                {summaryAnalysis.spatial && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Spatial Extent:</span>
                    <span style={{ color: 'var(--text-primary)' }}>
                      {summaryAnalysis.spatial.spatial_extent?.min_lat?.toFixed(1) ?? '—'}° to {summaryAnalysis.spatial.spatial_extent?.max_lat?.toFixed(1) ?? '—'}°N
                    </span>
                  </div>
                )}
                {summaryAnalysis.temporal && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Time Slices:</span>
                    <span style={{ color: 'var(--text-primary)' }}>
                      {summaryAnalysis.temporal.temporal_extent?.time_steps_count || 1}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 4. Dataset Provenance & Coverage (Progressive Disclosure - Collapsed by default) */}
      <div className="surface-card" style={{
        backgroundColor: 'var(--bg-surface)',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-default)',
        overflow: 'hidden',
      }}>
        <button
          onClick={() => setIsProvenanceOpen((prev) => !prev)}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.75rem 0.875rem',
            background: 'none',
            border: 'none',
            color: 'var(--accent-cyan)',
            cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.375rem',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}>
            <Database size={14} />
            PROVENANCE & COVERAGE
          </div>
          {isProvenanceOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>

        {isProvenanceOpen && (
          <div style={{ padding: '0 0.875rem 0.875rem' }}>
            {dataset ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.75rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Source: </span>
                  <span style={{ color: 'var(--text-secondary)' }}>{dataset.source || 'Copernicus Marine'}</span>
                </div>
                {spatial && (
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Spatial Extent: </span>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      [{(spatial.min_lat ?? spatial.latitude_min ?? -90).toFixed(1)}° to {(spatial.max_lat ?? spatial.latitude_max ?? 90).toFixed(1)}°N, {(spatial.min_lon ?? spatial.longitude_min ?? -180).toFixed(1)}° to {(spatial.max_lon ?? spatial.longitude_max ?? 180).toFixed(1)}°E]
                    </div>
                  </div>
                )}
                {temporal && (
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Temporal Extent: </span>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {(temporal.start ?? temporal.start_time ?? '—').split('T')[0]} to {(temporal.end ?? temporal.end_time ?? '—').split('T')[0]}
                    </div>
                  </div>
                )}
                {dataset.status && (
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Status: </span>
                    <span style={{ color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)' }}>{dataset.status.toUpperCase()}</span>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                No dataset loaded.
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
