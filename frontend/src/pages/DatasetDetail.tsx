import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Layers, 
  Globe, 
  Clock, 
  Play
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { getDatasetMetadata, getDatasetVariables } from '../api/datasets';
import { getVariableDisplay } from '../utils/variableNames';
import type { DatasetDetailResponse, DatasetVariableInfo } from '../types';

export const DatasetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [dataset, setDataset] = useState<DatasetDetailResponse | null>(null);
  const [variables, setVariables] = useState<DatasetVariableInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let isMounted = true;

    const fetchDetail = async () => {
      setLoading(true);
      setErrorMsg(null);
      try {
        const [meta, vars] = await Promise.all([
          getDatasetMetadata(id),
          getDatasetVariables(id),
        ]);
        if (!isMounted) return;
        setDataset(meta);
        setVariables(vars.variables || []);
      } catch (err: any) {
        if (isMounted) setErrorMsg(err.message || `Failed to fetch metadata for dataset ${id}`);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDetail();
    return () => { isMounted = false; };
  }, [id]);

  const spatial = dataset?.spatial_coverage || dataset?.spatial_extent;
  const temporal = dataset?.temporal_coverage || dataset?.temporal_extent;
  const depthLevels = dataset?.depth_levels || dataset?.depth_extent?.levels;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg-abyss)' }}>
      <Header />

      <main style={{ flex: 1, padding: '2rem 3rem', maxWidth: '1200px', margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        {/* Navigation Breadcrumb */}
        <div style={{ marginBottom: '1.5rem' }}>
          <Link
            to="/datasets"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.375rem',
              color: 'var(--text-secondary)',
              fontSize: '0.8125rem',
              textDecoration: 'none',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <ArrowLeft size={14} /> Back to Datasets Catalog
          </Link>
        </div>

        {errorMsg && <ErrorBanner message={errorMsg} />}

        {loading ? (
          <LoadingSkeleton type="card" rows={6} label="Loading scientific dataset metadata..." />
        ) : !dataset ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '3rem' }}>
            Dataset not found.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Header Title Section */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              backgroundColor: 'var(--bg-deep)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '1.5rem',
              flexWrap: 'wrap',
              gap: '1rem',
            }}>
              <div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  marginBottom: '0.5rem',
                }}>
                  <span style={{
                    fontSize: '0.6875rem',
                    fontFamily: 'var(--font-mono)',
                    padding: '0.125rem 0.5rem',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    color: 'var(--accent-cyan)',
                    border: '1px solid rgba(56, 189, 248, 0.25)',
                    borderRadius: 'var(--radius-sm)',
                  }}>
                    {dataset.source || 'COPERNICUS'}
                  </span>
                  <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    ID: {dataset.id || dataset.dataset_id}
                  </span>
                </div>
                <h1 style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '1.75rem',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  margin: 0,
                }}>
                  {dataset.name}
                </h1>
                {dataset.description && (
                  <p style={{
                    color: 'var(--text-secondary)',
                    fontSize: '0.875rem',
                    marginTop: '0.5rem',
                    maxWidth: '800px',
                    lineHeight: 1.5,
                  }}>
                    {dataset.description}
                  </p>
                )}
              </div>

              <Link
                to={`/workspace?dataset=${dataset.id || dataset.dataset_id}`}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.65rem 1.35rem',
                  backgroundColor: 'var(--accent-blue)',
                  color: '#fff',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  textDecoration: 'none',
                  boxShadow: '0 0 15px rgba(37, 99, 235, 0.3)',
                }}
              >
                <Play size={16} /> Open in Scientific Workspace
              </Link>
            </div>

            {/* Spatial & Temporal Extent Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
              {/* Spatial Extent */}
              <div className="surface-card" style={{
                backgroundColor: 'var(--bg-deep)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.375rem',
                  fontSize: '0.8125rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--accent-cyan)',
                  fontWeight: 600,
                  marginBottom: '0.875rem',
                }}>
                  <Globe size={16} /> SPATIAL EXTENT & BOUNDS
                </div>
                {spatial ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.8125rem', fontFamily: 'var(--font-mono)' }}>
                    <div>
                      Latitude: <span style={{ color: 'var(--text-primary)' }}>{(spatial.min_lat ?? spatial.latitude_min ?? -90).toFixed(1)}° to {(spatial.max_lat ?? spatial.latitude_max ?? 90).toFixed(1)}°N</span>
                    </div>
                    <div>
                      Longitude: <span style={{ color: 'var(--text-primary)' }}>{(spatial.min_lon ?? spatial.longitude_min ?? -180).toFixed(1)}° to {(spatial.max_lon ?? spatial.longitude_max ?? 180).toFixed(1)}°E</span>
                    </div>
                  </div>
                ) : (
                  <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Non-spatial dataset</div>
                )}
              </div>

              {/* Temporal & Vertical Extent */}
              <div className="surface-card" style={{
                backgroundColor: 'var(--bg-deep)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.375rem',
                  fontSize: '0.8125rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--accent-cyan)',
                  fontWeight: 600,
                  marginBottom: '0.875rem',
                }}>
                  <Clock size={16} /> TEMPORAL & VERTICAL EXTENT
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.8125rem', fontFamily: 'var(--font-mono)' }}>
                  <div>
                    Temporal Range: <span style={{ color: 'var(--text-primary)' }}>{(temporal?.start ?? temporal?.start_time ?? '—').split('T')[0]} to {(temporal?.end ?? temporal?.end_time ?? '—').split('T')[0]}</span>
                  </div>
                  <div>
                    Time Steps: <span style={{ color: 'var(--text-primary)' }}>{temporal?.time_steps_count ?? temporal?.total_timesteps ?? 1}</span>
                  </div>
                  <div>
                    Vertical Levels: <span style={{ color: 'var(--text-primary)' }}>{depthLevels?.length ?? 1}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Scientific Variables Table */}
            <div className="surface-card" style={{
              backgroundColor: 'var(--bg-deep)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '1.25rem',
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                fontSize: '0.8125rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--accent-cyan)',
                fontWeight: 600,
                marginBottom: '1rem',
              }}>
                <Layers size={16} /> SCIENTIFIC VARIABLES ({variables.length})
              </div>

              {variables.length === 0 ? (
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>No variables registered.</div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', fontFamily: 'var(--font-mono)' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-default)', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.6875rem' }}>
                        <th style={{ padding: '0.5rem' }}>VARIABLE</th>
                        <th style={{ padding: '0.5rem' }}>CODE</th>
                        <th style={{ padding: '0.5rem' }}>STANDARD / LONG NAME</th>
                        <th style={{ padding: '0.5rem' }}>UNITS</th>
                        <th style={{ padding: '0.5rem' }}>DIMENSIONS</th>
                        <th style={{ padding: '0.5rem' }}>SHAPE</th>
                        <th style={{ padding: '0.5rem' }}>DATA TYPE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {variables.map((v) => {
                        const rawCode = v.name || v.variable_name || '';
                        const meta = getVariableDisplay(rawCode);
                        return (
                          <tr key={rawCode} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                            <td style={{ padding: '0.625rem 0.5rem', color: 'var(--text-primary)', fontWeight: 600 }}>{meta.label}</td>
                            <td style={{ padding: '0.625rem 0.5rem', color: 'var(--accent-cyan)' }}>{rawCode}</td>
                            <td style={{ padding: '0.625rem 0.5rem', color: 'var(--text-secondary)' }}>{v.standard_name || v.long_name || meta.description || '—'}</td>
                            <td style={{ padding: '0.625rem 0.5rem', color: 'var(--accent-emerald)' }}>{v.units || 'unitless'}</td>
                            <td style={{ padding: '0.625rem 0.5rem', color: 'var(--text-secondary)' }}>{v.dimensions ? `(${v.dimensions.join(', ')})` : '—'}</td>
                            <td style={{ padding: '0.625rem 0.5rem', color: 'var(--text-secondary)' }}>{v.shape ? `[${v.shape.join(' × ')}]` : '—'}</td>
                            <td style={{ padding: '0.625rem 0.5rem', color: 'var(--text-muted)' }}>{v.data_type || v.dtype || '—'}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
