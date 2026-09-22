import React from 'react';
import { AlertTriangle, ShieldAlert, CheckCircle2 } from 'lucide-react';
import type { FrontendDatasetMetadata, VariableStatistics } from '../../types';
import { useAnalysis } from '../../context/AnalysisContext';

interface AnomalyViewerProps {
  dataset?: FrontendDatasetMetadata | null;
  variableName?: string;
  statistics?: VariableStatistics | null;
}

export const AnomalyViewer: React.FC<AnomalyViewerProps> = ({
  dataset: propDataset,
  variableName: propVar,
  statistics: propStats,
}) => {
  const context = useAnalysis();
  const dataset = propDataset !== undefined ? propDataset : context.metadata;
  const variableName = propVar ?? context.primaryVariable ?? 'Active Variable';
  const statistics = propStats !== undefined ? propStats : context.statistics;

  // Check if a registered climatological baseline exists in metadata attributes
  const baselineInfo = dataset?.metadata_json?.climatology_baseline || dataset?.metadata_json?.baseline_dataset;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      width: '100%',
      height: '100%',
      backgroundColor: 'var(--bg-deep)',
      borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border-default)',
      padding: '1.5rem',
      boxSizing: 'border-box',
      gap: '1.25rem',
    }}>
      {/* Header Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', letterSpacing: '0.06em' }}>
            SCIENTIFIC CLIMATOLOGY ENGINE
          </div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '0.25rem 0 0' }}>
            Anomaly Analysis: {variableName}
          </h2>
        </div>

        <div style={{
          padding: '0.25rem 0.625rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
          backgroundColor: baselineInfo ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
          color: baselineInfo ? 'var(--accent-emerald)' : 'var(--accent-amber)',
          border: `1px solid ${baselineInfo ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
        }}>
          {baselineInfo ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
          {baselineInfo ? 'BASELINE ACTIVE' : 'NO BASELINE REGISTERED'}
        </div>
      </div>

      {/* Baseline Verification Status */}
      {!baselineInfo ? (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: '3rem 2rem',
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          borderRadius: 'var(--radius-sm)',
          border: '1px dashed var(--border-default)',
          gap: '1rem',
          margin: 'auto 0',
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <ShieldAlert size={24} className="text-accent-amber" />
          </div>

          <div>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.05rem', color: 'var(--text-primary)', marginBottom: '0.375rem' }}>
              Anomaly analysis requires a baseline dataset.
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', maxWidth: '480px', lineHeight: 1.5, margin: '0 auto' }}>
              Scientific anomalies are strictly defined as [Observed Value − Baseline Climatology]. 
              No baseline climatology or long-term reference dataset has been linked to <strong>{dataset?.name || 'this dataset'}</strong>.
            </p>
          </div>

          <div style={{
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-secondary)',
            backgroundColor: 'rgba(0, 0, 0, 0.3)',
            padding: '0.5rem 1rem',
            borderRadius: 'var(--radius-sm)',
          }}>
            RULE: Climatological baselines are not fabricated or synthesized without empirical reference data.
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          <div className="surface-card" style={{ padding: '1rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>OBSERVED MEAN (x_obs)</span>
            <div style={{ fontSize: '1.25rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 600 }}>
              {statistics?.mean?.toFixed(3) ?? '—'} {statistics?.units}
            </div>
          </div>

          <div className="surface-card" style={{ padding: '1rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>CLIMATOLOGY BASELINE (x_base)</span>
            <div style={{ fontSize: '1.25rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontWeight: 600 }}>
              {baselineInfo.mean_value?.toFixed(3) ?? '—'} {statistics?.units}
            </div>
          </div>

          <div className="surface-card" style={{ padding: '1rem', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>ANOMALY (Δ)</span>
            <div style={{ fontSize: '1.25rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-rose)', fontWeight: 600 }}>
              {statistics?.mean && baselineInfo.mean_value ? (statistics.mean - baselineInfo.mean_value).toFixed(3) : '—'} {statistics?.units}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
