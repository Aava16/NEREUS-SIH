import React from 'react';
import { Database, Compass, AlertCircle, RefreshCw, Info, Sparkles } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: 'database' | 'compass' | 'alert' | 'info' | 'sparkles';
  actionLabel?: string;
  onAction?: () => void;
  variant?: 'default' | 'card' | 'panel';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Scientific Data Registered',
  description = 'NEREUS is ready. Register a dataset to begin exploring oceanographic observations and fields.',
  icon = 'compass',
  actionLabel,
  onAction,
  variant = 'card',
}) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      padding: '3rem 2rem',
      borderRadius: 'var(--radius-lg)',
      backgroundColor: variant === 'card' ? 'rgba(8, 14, 30, 0.7)' : 'transparent',
      border: variant === 'card' ? '1px solid var(--border-subtle)' : 'none',
      backdropFilter: 'blur(8px)',
      maxWidth: '560px',
      margin: '0 auto',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Subtle Concentric Bathymetric Contour Rings */}
      <div style={{
        position: 'absolute',
        width: '300px',
        height: '300px',
        borderRadius: '50%',
        border: '1px dashed rgba(56, 189, 248, 0.08)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute',
        width: '180px',
        height: '180px',
        borderRadius: '50%',
        border: '1px solid rgba(56, 189, 248, 0.05)',
        pointerEvents: 'none',
      }} />

      {/* Floating Center Icon */}
      <div style={{
        position: 'relative',
        zIndex: 2,
        marginBottom: '1.25rem',
        width: '54px',
        height: '54px',
        borderRadius: '50%',
        backgroundColor: 'rgba(56, 189, 248, 0.08)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 0 20px rgba(56, 189, 248, 0.15)',
      }}>
        {icon === 'database' ? (
          <Database size={24} color="var(--accent-cyan)" />
        ) : icon === 'alert' ? (
          <AlertCircle size={24} color="var(--accent-amber)" />
        ) : icon === 'info' ? (
          <Info size={24} color="var(--accent-cyan)" />
        ) : icon === 'sparkles' ? (
          <Sparkles size={24} color="var(--accent-emerald)" />
        ) : (
          <Compass size={24} color="var(--accent-cyan)" />
        )}
      </div>

      <div style={{
        position: 'relative',
        zIndex: 2,
        fontSize: '0.6875rem',
        fontFamily: 'var(--font-mono)',
        color: 'var(--accent-cyan)',
        letterSpacing: '0.08em',
        marginBottom: '0.35rem',
      }}>
        INSTRUMENT STANDBY
      </div>

      <h3 style={{
        position: 'relative',
        zIndex: 2,
        fontFamily: 'var(--font-display)',
        fontSize: '1.1875rem',
        fontWeight: 600,
        color: 'var(--text-primary)',
        margin: '0 0 0.625rem',
        letterSpacing: '-0.01em',
      }}>
        {title}
      </h3>

      <p style={{
        position: 'relative',
        zIndex: 2,
        fontSize: '0.875rem',
        color: 'var(--text-secondary)',
        lineHeight: 1.6,
        margin: '0 0 1.5rem',
        maxWidth: '440px',
      }}>
        {description}
      </p>

      {actionLabel && onAction && (
        <button
          onClick={onAction}
          style={{
            position: 'relative',
            zIndex: 2,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.55rem 1.25rem',
            backgroundColor: 'rgba(56, 189, 248, 0.15)',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--accent-cyan)',
            fontWeight: 500,
            fontSize: '0.8125rem',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <RefreshCw size={13} />
          <span>{actionLabel}</span>
        </button>
      )}
    </div>
  );
};
