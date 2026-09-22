import React from 'react';
import { 
  Bookmark, 
  MessageSquarePlus, 
  Download, 
  Database, 
  RotateCcw 
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';

export const QuickActionBar: React.FC = () => {
  const {
    setIsSnapshotModalOpen,
    setIsAnnotationDrawerOpen,
    setIsProvenanceModalOpen,
    setIsExportModalOpen,
    resetWorkspace,
  } = useAnalysis();

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.375rem',
      backgroundColor: 'var(--bg-deep)',
      padding: '0.25rem 0.5rem',
      borderRadius: 'var(--radius-sm)',
      border: '1px solid var(--border-default)',
    }}>
      {/* Snapshots Button */}
      <button
        onClick={() => setIsSnapshotModalOpen(true)}
        title="Saved Analysis Snapshots"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.3125rem',
          padding: '0.3rem 0.5rem',
          backgroundColor: 'transparent',
          border: '1px solid transparent',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--text-secondary)',
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
          cursor: 'pointer',
        }}
      >
        <Bookmark size={13} className="text-accent-cyan" />
        <span>Snapshots</span>
      </button>

      {/* Annotations Button */}
      <button
        onClick={() => setIsAnnotationDrawerOpen(true)}
        title="Record Observation / Field Notes"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.3125rem',
          padding: '0.3rem 0.5rem',
          backgroundColor: 'transparent',
          border: '1px solid transparent',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--text-secondary)',
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
          cursor: 'pointer',
        }}
      >
        <MessageSquarePlus size={13} className="text-accent-cyan" />
        <span>Annotate</span>
      </button>

      {/* Provenance Button */}
      <button
        onClick={() => setIsProvenanceModalOpen(true)}
        title="View Scientific Provenance & Metadata"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.3125rem',
          padding: '0.3rem 0.5rem',
          backgroundColor: 'transparent',
          border: '1px solid transparent',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--text-secondary)',
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
          cursor: 'pointer',
        }}
      >
        <Database size={13} className="text-accent-cyan" />
        <span>Provenance</span>
      </button>

      {/* Export Button */}
      <button
        onClick={() => setIsExportModalOpen(true)}
        title="Export Analysis Data (CSV, JSON, Report, PNG)"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.3125rem',
          padding: '0.3rem 0.5rem',
          backgroundColor: 'transparent',
          border: '1px solid transparent',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--text-secondary)',
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
          cursor: 'pointer',
        }}
      >
        <Download size={13} className="text-accent-cyan" />
        <span>Export</span>
      </button>

      <div style={{ width: '1px', height: '14px', backgroundColor: 'var(--border-subtle)', margin: '0 0.125rem' }} />

      {/* Reset Workspace */}
      <button
        onClick={resetWorkspace}
        title="Reset workspace filters to initial defaults"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.3125rem',
          padding: '0.3rem 0.5rem',
          backgroundColor: 'transparent',
          border: '1px solid transparent',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--text-muted)',
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
          cursor: 'pointer',
        }}
      >
        <RotateCcw size={12} />
        <span>Reset</span>
      </button>
    </div>
  );
};
