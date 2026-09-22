import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  ArrowRight,
  RefreshCw,
  CheckCircle2,
  FileCode
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { listDatasets } from '../api/datasets';
import type { DatasetListItem } from '../types';

export const DatasetExplorer: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sourceFilter, setSourceFilter] = useState<string>('ALL');

  const fetchCatalog = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await listDatasets();
      setDatasets(res.items || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch datasets catalog from NEREUS API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalog();
  }, []);

  // Filter datasets
  const sources = Array.from(new Set(datasets.map((d) => d.source).filter((s): s is string => Boolean(s))));
  const filteredDatasets = datasets.filter((d) => {
    const matchesSearch = d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (d.source && d.source.toLowerCase().includes(searchQuery.toLowerCase())) ||
                          (d.description && d.description.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesSource = sourceFilter === 'ALL' || d.source === sourceFilter;
    return matchesSearch && matchesSource;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg-abyss)' }}>
      <Header />

      <main style={{ flex: 1, padding: '2rem 3rem', maxWidth: '1400px', margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        {/* Page Title & Search Bar */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem',
          marginBottom: '2rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
            <div>
              <div style={{
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--accent-cyan)',
                letterSpacing: '0.08em',
                marginBottom: '0.25rem',
              }}>
                CANONICAL REPOSITORY
              </div>
              <h1 style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.875rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                letterSpacing: '-0.02em',
                margin: 0,
              }}>
                Scientific Dataset Explorer
              </h1>
            </div>

            <button
              onClick={fetchCatalog}
              className="btn-outline"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                padding: '0.5rem 0.875rem',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: '0.8125rem',
              }}
            >
              <RefreshCw size={14} /> Refresh Catalog
            </button>
          </div>

          {/* Search & Filter Controls */}
          <div style={{
            display: 'flex',
            gap: '1rem',
            alignItems: 'center',
            backgroundColor: 'var(--bg-deep)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              flex: 1,
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.5rem 0.75rem',
            }}>
              <Search size={16} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Search datasets by name, source, or variable..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  background: 'none',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                  width: '100%',
                }}
              />
            </div>

            {sources.length > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  SOURCE:
                </span>
                <select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.5rem 0.75rem',
                    color: 'var(--text-primary)',
                    fontSize: '0.8125rem',
                  }}
                >
                  <option value="ALL">All Sources</option>
                  {sources.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Error Banner */}
        {errorMsg && <ErrorBanner message={errorMsg} onRetry={fetchCatalog} />}

        {/* Content Body */}
        {loading ? (
          <LoadingSkeleton type="card" rows={4} label="Fetching scientific datasets from PostgreSQL..." />
        ) : filteredDatasets.length === 0 ? (
          <EmptyState
            variant="card"
            title={searchQuery ? 'No Matching Datasets' : 'No Registered Scientific Datasets'}
            description={
              searchQuery
                ? `No datasets matched query "${searchQuery}". Try modifying your filter criteria.`
                : 'The NEREUS scientific data catalog currently has no registered NetCDF/Zarr datasets in PostgreSQL.'
            }
            actionLabel={searchQuery ? 'Clear Search' : 'Refresh Catalog'}
            onAction={() => {
              if (searchQuery) setSearchQuery('');
              else fetchCatalog();
            }}
          />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(420px, 1fr))', gap: '1.25rem' }}>
            {filteredDatasets.map((dataset) => (
              <div
                key={dataset.id}
                className="surface-card"
                style={{
                  backgroundColor: 'var(--bg-deep)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  transition: 'border-color 0.2s ease, transform 0.15s ease',
                }}
              >
                {/* Top Badge & Title */}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{
                      fontSize: '0.6875rem',
                      fontFamily: 'var(--font-mono)',
                      padding: '0.125rem 0.5rem',
                      backgroundColor: 'rgba(56, 189, 248, 0.1)',
                      color: 'var(--accent-cyan)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      borderRadius: 'var(--radius-sm)',
                    }}>
                      {dataset.source || 'UNKNOWN SOURCE'}
                    </span>
                    <span style={{
                      fontSize: '0.6875rem',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--accent-emerald)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                    }}>
                      <CheckCircle2 size={12} /> {dataset.status?.toUpperCase() || 'READY'}
                    </span>
                  </div>

                  <h3 style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: '1.125rem',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    margin: 0,
                  }}>
                    {dataset.name}
                  </h3>
                  {dataset.description && (
                    <p style={{
                      fontSize: '0.8125rem',
                      color: 'var(--text-secondary)',
                      marginTop: '0.375rem',
                      lineHeight: 1.4,
                      maxHeight: '40px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}>
                      {dataset.description}
                    </p>
                  )}
                </div>

                {/* Spatial / Temporal Meta Grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '0.5rem',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)',
                  backgroundColor: 'rgba(15, 23, 42, 0.5)',
                  padding: '0.625rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>COVERAGE: </span>
                    <span style={{ color: 'var(--text-primary)' }}>
                      {dataset.spatial_coverage ? 'Spatial Grid' : 'Standard'}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>VARIABLES: </span>
                    <span style={{ color: 'var(--accent-cyan)' }}>
                      {dataset.variable_names?.length || '—'} vars
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '0.75rem', marginTop: 'auto', paddingTop: '0.5rem' }}>
                  <Link
                    to={`/datasets/${dataset.id}`}
                    style={{
                      flex: 1,
                      textAlign: 'center',
                      padding: '0.5rem',
                      backgroundColor: 'var(--bg-surface)',
                      border: '1px solid var(--border-default)',
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--text-secondary)',
                      fontSize: '0.8125rem',
                      textDecoration: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.375rem',
                    }}
                  >
                    <FileCode size={14} /> Detail
                  </Link>
                  <Link
                    to={`/?dataset=${dataset.id}`}
                    style={{
                      flex: 2,
                      textAlign: 'center',
                      padding: '0.5rem',
                      backgroundColor: 'var(--accent-blue)',
                      border: '1px solid transparent',
                      borderRadius: 'var(--radius-sm)',
                      color: '#ffffff',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      textDecoration: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.375rem',
                    }}
                  >
                    Open in Canvas <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};
