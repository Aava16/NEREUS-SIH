import React from 'react';
import { 
  Database, 
  X, 
  Globe, 
  Clock, 
  Cpu, 
  Layers, 
  FileText, 
  ShieldCheck, 
  Download 
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';
import { exportObjectAsJson } from '../../utils/exportUtils';

export const ProvenanceModal: React.FC = () => {
  const {
    isProvenanceModalOpen,
    setIsProvenanceModalOpen,
    metadata,
    variables,
    datasetId,
  } = useAnalysis();

  if (!isProvenanceModalOpen) return null;

  const spatial = metadata?.spatial_coverage || metadata?.spatial_extent;
  const temporal = metadata?.temporal_coverage || metadata?.temporal_extent;
  const rawMeta = metadata?.metadata_json || {};

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(3, 7, 18, 0.75)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '780px',
        backgroundColor: 'var(--bg-deep)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
        display: 'flex',
        flexDirection: 'column',
        maxHeight: '85vh',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '1rem 1.25rem',
          borderBottom: '1px solid var(--border-subtle)',
          backgroundColor: 'var(--bg-surface)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Database size={18} className="text-accent-cyan" />
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              Dataset Provenance & Scientific Lineage
            </h2>
          </div>
          <button
            onClick={() => setIsProvenanceModalOpen(false)}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '0.25rem' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '1.25rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {metadata ? (
            <>
              {/* Primary Lineage Summary */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '0.75rem',
              }}>
                <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <ShieldCheck size={12} className="text-accent-emerald" /> CANONICAL DATASET ID
                  </span>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text-primary)', fontWeight: 600, marginTop: '0.25rem', wordBreak: 'break-all' }}>
                    {metadata.id || metadata.dataset_id || datasetId}
                  </div>
                </div>

                <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Cpu size={12} className="text-accent-cyan" /> SOURCE / OBSERVING PLATFORM
                  </span>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--accent-cyan)', fontWeight: 600, marginTop: '0.25rem' }}>
                    {metadata.source || 'Standard Repository'}
                  </div>
                </div>

                <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Globe size={12} className="text-accent-cyan" /> COORDINATE REFERENCE SYSTEM
                  </span>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text-primary)', fontWeight: 600, marginTop: '0.25rem' }}>
                    WGS 84 (EPSG:4326)
                  </div>
                </div>
              </div>

              {/* Spatial & Temporal Extents */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ padding: '0.875rem', backgroundColor: 'rgba(15, 23, 42, 0.6)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 600, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                    <Globe size={14} /> SPATIAL DOMAIN
                  </div>
                  {spatial ? (
                    <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <div>Latitude: [{(spatial.min_lat ?? spatial.latitude_min ?? -90).toFixed(2)}° to {(spatial.max_lat ?? spatial.latitude_max ?? 90).toFixed(2)}°N]</div>
                      <div>Longitude: [{(spatial.min_lon ?? spatial.longitude_min ?? -180).toFixed(2)}° to {(spatial.max_lon ?? spatial.longitude_max ?? 180).toFixed(2)}°E]</div>
                    </div>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Non-spatial array</span>
                  )}
                </div>

                <div style={{ padding: '0.875rem', backgroundColor: 'rgba(15, 23, 42, 0.6)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 600, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                    <Clock size={14} /> TEMPORAL SPAN
                  </div>
                  {temporal ? (
                    <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <div>Range: {(temporal.start ?? temporal.start_time ?? '—').split('T')[0]} to {(temporal.end ?? temporal.end_time ?? '—').split('T')[0]}</div>
                      <div>Steps: {temporal.time_steps_count ?? temporal.total_timesteps ?? 1} total slices</div>
                    </div>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Static time</span>
                  )}
                </div>
              </div>

              {/* Registered Scientific Variables Table */}
              <div style={{ padding: '0.875rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 600, marginBottom: '0.625rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                  <Layers size={14} /> REGISTERED SCIENTIFIC VARIABLES ({variables.length})
                </div>
                <div style={{ maxHeight: '160px', overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-default)', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.6875rem' }}>
                        <th style={{ padding: '0.35rem 0.5rem' }}>VARIABLE</th>
                        <th style={{ padding: '0.35rem 0.5rem' }}>STANDARD NAME</th>
                        <th style={{ padding: '0.35rem 0.5rem' }}>UNITS</th>
                        <th style={{ padding: '0.35rem 0.5rem' }}>DIMENSIONS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {variables.map((v) => (
                        <tr key={v.name || v.variable_name} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '0.4rem 0.5rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>{v.name || v.variable_name}</td>
                          <td style={{ padding: '0.4rem 0.5rem', color: 'var(--text-secondary)' }}>{v.standard_name || v.long_name || '—'}</td>
                          <td style={{ padding: '0.4rem 0.5rem', color: 'var(--accent-emerald)' }}>{v.units || 'unitless'}</td>
                          <td style={{ padding: '0.4rem 0.5rem', color: 'var(--text-muted)' }}>({v.dimensions?.join(', ') || '—'})</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Raw CF Metadata Attributes JSON */}
              {Object.keys(rawMeta).length > 0 && (
                <div style={{ padding: '0.875rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                      <FileText size={14} /> CF & GLOBAL NETCDF ATTRIBUTES
                    </span>
                    <button
                      onClick={() => exportObjectAsJson(rawMeta, `nereus_dataset_${datasetId}_metadata.json`)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        padding: '0.2rem 0.5rem',
                        backgroundColor: 'rgba(56, 189, 248, 0.1)',
                        border: '1px solid rgba(56, 189, 248, 0.2)',
                        borderRadius: 'var(--radius-sm)',
                        color: 'var(--accent-cyan)',
                        fontSize: '0.6875rem',
                        fontFamily: 'var(--font-mono)',
                        cursor: 'pointer',
                      }}
                    >
                      <Download size={11} /> Export JSON
                    </button>
                  </div>
                  <pre style={{
                    margin: 0,
                    padding: '0.625rem',
                    backgroundColor: 'var(--bg-abyss)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.6875rem',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-secondary)',
                    maxHeight: '140px',
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}>
                    {JSON.stringify(rawMeta, null, 2)}
                  </pre>
                </div>
              )}
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
              No dataset loaded.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
