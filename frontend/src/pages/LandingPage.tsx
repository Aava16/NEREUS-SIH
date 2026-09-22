import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Compass, 
  Layers, 
  Activity, 
  Wind, 
  ArrowRight, 
  Database, 
  CheckCircle2, 
  Globe
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { OceanHeroCanvas } from '../components/common/OceanHeroCanvas';
import { listDatasets } from '../api/datasets';
import type { DatasetListItem } from '../types';

export const LandingPage: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    listDatasets()
      .then((res) => {
        if (isMounted) setDatasets(res.items || []);
      })
      .catch(() => {
        if (isMounted) setDatasets([]);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      backgroundColor: 'var(--bg-abyss)',
      color: 'var(--text-primary)',
      position: 'relative',
      overflowX: 'hidden',
    }}>
      {/* Dynamic Background */}
      <OceanHeroCanvas />

      {/* Global Header */}
      <div style={{ position: 'relative', zIndex: 10 }}>
        <Header datasets={datasets} />
      </div>

      {/* Hero Section */}
      <main style={{
        position: 'relative',
        zIndex: 5,
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3.5rem 1.5rem 4.5rem',
        maxWidth: '1280px',
        margin: '0 auto',
        width: '100%',
        boxSizing: 'border-box',
      }}>
        {/* Subtle Pre-Header Badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.3rem 0.85rem',
          borderRadius: '9999px',
          backgroundColor: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          color: 'var(--accent-cyan)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          letterSpacing: '0.06em',
          marginBottom: '1.5rem',
          boxShadow: '0 0 20px rgba(56, 189, 248, 0.1)',
        }}>
          <Compass size={14} className="animate-spin-slow" />
          <span>NEREUS — OCEAN DATA INTELLIGENCE</span>
        </div>

        {/* Hero Title */}
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(2.2rem, 5vw, 3.8rem)',
          fontWeight: 700,
          textAlign: 'center',
          lineHeight: 1.15,
          letterSpacing: '-0.03em',
          maxWidth: '900px',
          margin: '0 0 1.25rem',
          background: 'linear-gradient(180deg, #ffffff 30%, #94a3b8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          Scientific Ocean Exploration & Analytical Intelligence
        </h1>

        {/* Supporting Tagline */}
        <p style={{
          fontSize: 'clamp(1rem, 1.8vw, 1.25rem)',
          color: 'var(--text-secondary)',
          textAlign: 'center',
          maxWidth: '680px',
          lineHeight: 1.6,
          margin: '0 0 2.25rem',
          fontWeight: 400,
        }}>
          <strong style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>Explore.</strong>{' '}
          <strong style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Analyze.</strong>{' '}
          <strong style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>Understand.</strong>{' '}
          Seamlessly ingest, process, and interrogate multi-dimensional oceanographic arrays, satellite observations, and in-situ sensor networks.
        </p>

        {/* Direct Action Buttons */}
        <div style={{
          display: 'flex',
          gap: '1rem',
          flexWrap: 'wrap',
          justifyContent: 'center',
          marginBottom: '4rem',
        }}>
          <Link
            to="/workspace"
            className="btn-primary-glow"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.6rem',
              padding: '0.85rem 1.75rem',
              backgroundColor: 'var(--accent-cyan)',
              color: '#030712',
              fontWeight: 600,
              fontSize: '0.9375rem',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
              boxShadow: '0 0 25px rgba(56, 189, 248, 0.35)',
              transition: 'all 0.2s ease',
            }}
          >
            <span>Launch Scientific Workspace</span>
            <ArrowRight size={17} />
          </Link>

          <Link
            to="/datasets"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.6rem',
              padding: '0.85rem 1.6rem',
              backgroundColor: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid var(--border-default)',
              color: 'var(--text-primary)',
              fontWeight: 500,
              fontSize: '0.9375rem',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
              backdropFilter: 'blur(8px)',
              transition: 'all 0.2s ease',
            }}
          >
            <Database size={16} color="var(--accent-cyan)" />
            <span>Browse Catalog ({loading ? '...' : datasets.length})</span>
          </Link>
        </div>

        {/* 4 Core Modalities Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '1.25rem',
          width: '100%',
          maxWidth: '1200px',
          marginBottom: '3.5rem',
        }}>
          {/* Card 1 */}
          <div style={{
            backgroundColor: 'rgba(14, 22, 41, 0.65)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.5rem',
            backdropFilter: 'blur(12px)',
            transition: 'transform 0.2s ease, border-color 0.2s ease',
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(56, 189, 248, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
              border: '1px solid rgba(56, 189, 248, 0.2)',
            }}>
              <Globe size={20} color="var(--accent-cyan)" />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Spatial Grid Fields
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
              Perceptually uniform colormaps (thermal, haline, coolwarm) with interactive bounding-box selection and Level-of-Detail decimation.
            </p>
          </div>

          {/* Card 2 */}
          <div style={{
            backgroundColor: 'rgba(14, 22, 41, 0.65)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.5rem',
            backdropFilter: 'blur(12px)',
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
              border: '1px solid rgba(16, 185, 129, 0.2)',
            }}>
              <Layers size={20} color="var(--accent-emerald)" />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              4D Depth Profiles
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
              Continuous water-column vertical soundings, mixed layer thermocline analysis, and great-circle transect cross-sections.
            </p>
          </div>

          {/* Card 3 */}
          <div style={{
            backgroundColor: 'rgba(14, 22, 41, 0.65)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.5rem',
            backdropFilter: 'blur(12px)',
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(245, 158, 11, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
              border: '1px solid rgba(245, 158, 11, 0.2)',
            }}>
              <Activity size={20} color="var(--accent-amber)" />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              In-Situ Time Series
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
              Synchronized temporal playback, climatological baseline anomaly detection, and station sensor point probing.
            </p>
          </div>

          {/* Card 4 */}
          <div style={{
            backgroundColor: 'rgba(14, 22, 41, 0.65)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.5rem',
            backdropFilter: 'blur(12px)',
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
              border: '1px solid rgba(99, 102, 241, 0.2)',
            }}>
              <Wind size={20} color="var(--accent-indigo)" />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Hydrodynamic Currents
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
              Integrated U/V/W vector fields with speed cutoff thresholding, velocity HUDs, and dynamic difference mapping (Δ = A − B).
            </p>
          </div>
        </div>

        {/* Scientific Pipeline Badge Summary */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.75rem',
          flexWrap: 'wrap',
          padding: '1rem 1.5rem',
          backgroundColor: 'rgba(8, 14, 30, 0.75)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          fontSize: '0.8125rem',
          color: 'var(--text-secondary)',
          fontFamily: 'var(--font-mono)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <CheckCircle2 size={14} color="var(--accent-emerald)" />
            <span>PostgreSQL + PostGIS (WGS 84)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <CheckCircle2 size={14} color="var(--accent-emerald)" />
            <span>CF-1.8 NetCDF & Zarr Array Engine</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <CheckCircle2 size={14} color="var(--accent-emerald)" />
            <span>Decimated LOD REST Delivery</span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        position: 'relative',
        zIndex: 5,
        borderTop: '1px solid var(--border-subtle)',
        padding: '1.25rem 2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.75rem',
        color: 'var(--text-muted)',
        fontFamily: 'var(--font-mono)',
        backgroundColor: 'rgba(3, 7, 18, 0.85)',
      }}>
        <div>NEREUS-SIH v0.1.0 • Smart India Hackathon Scientific Edition</div>
        <div>Perceptually Uniform • Memory Bounded • Zero Mock Data</div>
      </footer>
    </div>
  );
};
