import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Waves, Database, Compass, Activity, CheckCircle2, AlertCircle } from 'lucide-react';
import { checkHealth, checkDbHealth } from '../../api/health';
import { QuickActionBar } from '../research/QuickActionBar';
import type { DatasetListItem } from '../../types';

interface HeaderProps {
  datasets?: DatasetListItem[];
  selectedDatasetId?: string | null;
  onSelectDataset?: (id: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  datasets = [],
  selectedDatasetId,
  onSelectDataset,
}) => {
  const location = useLocation();
  const [apiStatus, setApiStatus] = useState<'healthy' | 'degraded' | 'offline' | 'checking'>('checking');
  const [dbStatus, setDbStatus] = useState<'healthy' | 'degraded' | 'offline' | 'checking'>('checking');

  useEffect(() => {
    let isMounted = true;

    const verifySystemStatus = async () => {
      try {
        const health = await checkHealth();
        if (isMounted) {
          setApiStatus(health.status === 'healthy' ? 'healthy' : 'degraded');
        }
      } catch {
        if (isMounted) setApiStatus('offline');
      }

      try {
        const dbHealth = await checkDbHealth();
        if (isMounted) {
          setDbStatus(dbHealth.status === 'healthy' ? 'healthy' : 'degraded');
        }
      } catch {
        if (isMounted) setDbStatus('offline');
      }
    };

    verifySystemStatus();
    const interval = setInterval(verifySystemStatus, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0.625rem 1.25rem',
      backgroundColor: 'var(--bg-deep)',
      borderBottom: '1px solid var(--border-subtle)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(8px)',
    }}>
      {/* Brand & Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', textDecoration: 'none' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-sm)',
            background: 'linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-cyan) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 12px rgba(56, 189, 248, 0.3)',
          }}>
            <Waves size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 700,
              fontSize: '1.0625rem',
              letterSpacing: '0.08em',
              color: 'var(--text-primary)',
              lineHeight: 1.1,
            }}>
              NEREUS
            </div>
            <div style={{
              fontSize: '0.6875rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--accent-cyan)',
              letterSpacing: '0.06em',
            }}>
              OCEAN OBSERVATORY
            </div>
          </div>
        </Link>

        {/* Global Dataset Quick Selector */}
        {datasets.length > 0 && onSelectDataset && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginLeft: '1rem',
            paddingLeft: '1rem',
            borderLeft: '1px solid var(--border-subtle)',
          }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              DATASET:
            </span>
            <select
              value={selectedDatasetId || ''}
              onChange={(e) => onSelectDataset(e.target.value)}
              className="select-input"
              style={{
                fontSize: '0.8125rem',
                padding: '0.25rem 0.625rem',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                maxWidth: '220px',
              }}
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Navigation, Research Tools & System Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <nav style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
            <Link
              to="/"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                padding: '0.375rem 0.625rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8125rem',
                fontWeight: 500,
                textDecoration: 'none',
                color: location.pathname === '/' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                backgroundColor: location.pathname === '/' ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                border: location.pathname === '/' ? '1px solid rgba(56, 189, 248, 0.25)' : '1px solid transparent',
                transition: 'all 0.15s ease',
              }}
            >
              <Waves size={14} />
              Overview
            </Link>
            <Link
              to="/workspace"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                padding: '0.375rem 0.625rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8125rem',
                fontWeight: 500,
                textDecoration: 'none',
                color: location.pathname === '/workspace' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                backgroundColor: location.pathname === '/workspace' ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                border: location.pathname === '/workspace' ? '1px solid rgba(56, 189, 248, 0.25)' : '1px solid transparent',
                transition: 'all 0.15s ease',
              }}
            >
              <Compass size={14} />
              Scientific Workspace
            </Link>
            <Link
              to="/datasets"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                padding: '0.375rem 0.625rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8125rem',
                fontWeight: 500,
                textDecoration: 'none',
                color: location.pathname.startsWith('/datasets') ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                backgroundColor: location.pathname.startsWith('/datasets') ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                border: location.pathname.startsWith('/datasets') ? '1px solid rgba(56, 189, 248, 0.25)' : '1px solid transparent',
                transition: 'all 0.15s ease',
              }}
            >
              <Database size={14} />
              Catalog
            </Link>
          </nav>

          {/* Quick Research Actions Bar */}
          {(location.pathname === '/workspace' || location.pathname.startsWith('/datasets/')) && <QuickActionBar />}
        </div>

        {/* Backend & DB Health Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.875rem',
          padding: '0.25rem 0.75rem',
          backgroundColor: 'rgba(15, 23, 42, 0.7)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.6875rem',
        }}>
          {/* API Health */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
            <Activity size={12} color="var(--text-muted)" />
            <span style={{ color: 'var(--text-muted)' }}>API:</span>
            {apiStatus === 'healthy' ? (
              <span style={{ color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '2px' }}>
                <CheckCircle2 size={11} /> ONLINE
              </span>
            ) : apiStatus === 'checking' ? (
              <span style={{ color: 'var(--accent-amber)' }}>...</span>
            ) : (
              <span style={{ color: 'var(--accent-rose)', display: 'flex', alignItems: 'center', gap: '2px' }}>
                <AlertCircle size={11} /> ERROR
              </span>
            )}
          </div>

          <span style={{ color: 'var(--border-default)' }}>|</span>

          {/* DB Health */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
            <Database size={12} color="var(--text-muted)" />
            <span style={{ color: 'var(--text-muted)' }}>POSTGIS:</span>
            {dbStatus === 'healthy' ? (
              <span style={{ color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '2px' }}>
                <CheckCircle2 size={11} /> READY
              </span>
            ) : dbStatus === 'checking' ? (
              <span style={{ color: 'var(--accent-amber)' }}>...</span>
            ) : (
              <span style={{ color: 'var(--accent-rose)', display: 'flex', alignItems: 'center', gap: '2px' }}>
                <AlertCircle size={11} /> UNREACHABLE
              </span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
