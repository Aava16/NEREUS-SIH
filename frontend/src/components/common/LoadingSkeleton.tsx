import React from 'react';

interface LoadingSkeletonProps {
  type?: 'card' | 'text' | 'grid' | 'chart' | 'stats' | 'field';
  rows?: number;
  label?: string;
  step?: 'DATA' | 'FIELD' | 'ANALYSIS';
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  type = 'card',
  rows = 3,
  label = 'Accessing ocean scientific array...',
  step,
}) => {
  return (
    <div style={{
      padding: '1.75rem',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '1.25rem',
      width: '100%',
      boxSizing: 'border-box',
    }}>
      {/* Signature Scientific Radar / Grid Field Loader */}
      <div style={{
        position: 'relative',
        width: '64px',
        height: '64px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        {/* Outer Ring */}
        <div style={{
          position: 'absolute',
          inset: 0,
          borderRadius: '50%',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          animation: 'ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite',
        }} />
        {/* Middle Ring */}
        <div style={{
          position: 'absolute',
          inset: '8px',
          borderRadius: '50%',
          border: '1.5px dashed rgba(56, 189, 248, 0.5)',
          animation: 'spin 6s linear infinite',
        }} />
        {/* Center Crosshair Coordinate Marker */}
        <div style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: 'var(--accent-cyan)',
          boxShadow: '0 0 12px var(--accent-cyan)',
        }} />
      </div>

      {/* Label and Pipeline Step Indicator */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '0.4rem',
      }}>
        <div style={{
          fontSize: '0.8125rem',
          color: 'var(--text-primary)',
          fontFamily: 'var(--font-mono)',
          letterSpacing: '0.04em',
          fontWeight: 500,
        }}>
          {label}
        </div>

        {/* DATA -> FIELD -> ANALYSIS Scientific Pipeline Tracker */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-muted)',
        }}>
          <span style={{ color: step === 'DATA' || !step ? 'var(--accent-cyan)' : 'var(--text-secondary)' }}>
            [DATA]
          </span>
          <span>→</span>
          <span style={{ color: step === 'FIELD' ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
            [FIELD]
          </span>
          <span>→</span>
          <span style={{ color: step === 'ANALYSIS' ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
            [ANALYSIS]
          </span>
        </div>
      </div>

      {type === 'chart' && (
        <div style={{
          width: '100%',
          height: '240px',
          background: 'linear-gradient(90deg, rgba(15, 24, 45, 0.4) 25%, rgba(30, 46, 82, 0.6) 50%, rgba(15, 24, 45, 0.4) 75%)',
          backgroundSize: '200% 100%',
          animation: 'shimmer 2s infinite',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }} />
      )}

      {type === 'grid' && (
        <div style={{
          width: '100%',
          height: '380px',
          background: 'linear-gradient(90deg, rgba(8, 14, 30, 0.6) 25%, rgba(20, 32, 58, 0.8) 50%, rgba(8, 14, 30, 0.6) 75%)',
          backgroundSize: '200% 100%',
          animation: 'shimmer 2s infinite',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }} />
      )}

      {type === 'stats' && (
        <div style={{
          width: '100%',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
          gap: '0.75rem',
        }}>
          {[1, 2, 3, 4, 5, 6].map((idx) => (
            <div
              key={idx}
              style={{
                height: '70px',
                background: 'rgba(15, 24, 45, 0.5)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                animation: 'pulse 1.8s infinite',
              }}
            />
          ))}
        </div>
      )}

      {type === 'card' && (
        <div style={{
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}>
          {Array.from({ length: rows }).map((_, i) => (
            <div
              key={i}
              style={{
                height: '48px',
                background: 'rgba(15, 24, 45, 0.4)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                animation: 'pulse 1.8s infinite',
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};
