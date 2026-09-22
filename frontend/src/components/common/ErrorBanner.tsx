import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorBannerProps {
  title?: string;
  message: string;
  detail?: string;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  title = 'Scientific Field Notice',
  message,
  detail,
  onRetry,
}) => {
  return (
    <div style={{
      padding: '0.85rem 1.15rem',
      borderRadius: 'var(--radius-md)',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      border: '1px solid rgba(245, 158, 11, 0.35)',
      color: 'var(--text-primary)',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.35rem',
      margin: '0.4rem 0',
      backdropFilter: 'blur(8px)',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertCircle size={16} color="var(--accent-amber)" style={{ flexShrink: 0 }} />
          <strong style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--accent-amber)', fontFamily: 'var(--font-mono)', letterSpacing: '0.04em' }}>
            {title.toUpperCase()}
          </strong>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              background: 'rgba(245, 158, 11, 0.12)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              color: 'var(--accent-amber)',
              fontSize: '0.6875rem',
              padding: '0.2rem 0.55rem',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              fontWeight: 500,
              fontFamily: 'var(--font-mono)',
              transition: 'all 0.15s ease',
            }}
          >
            <RefreshCw size={11} />
            <span>Retry Query</span>
          </button>
        )}
      </div>

      <p style={{ fontSize: '0.8125rem', margin: 0, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
        {message}
      </p>

      {detail && (
        <pre style={{
          fontSize: '0.6875rem',
          fontFamily: 'var(--font-mono)',
          padding: '0.4rem 0.6rem',
          background: 'rgba(3, 7, 18, 0.6)',
          borderRadius: 'var(--radius-sm)',
          overflowX: 'auto',
          margin: '0.25rem 0 0',
          color: 'var(--text-muted)',
          border: '1px solid var(--border-subtle)',
        }}>
          {detail}
        </pre>
      )}
    </div>
  );
};
