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
  Globe,
  SlidersHorizontal,
  LineChart
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
      {/* Dynamic Oceanic Background Canvas */}
      <OceanHeroCanvas />

      {/* Global Header */}
      <div style={{ position: 'relative', zIndex: 10 }}>
        <Header datasets={datasets} />
      </div>

      {/* Main Hero Section */}
      <main style={{
        position: 'relative',
        zIndex: 5,
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 1.5rem 4rem',
        maxWidth: '1240px',
        margin: '0 auto',
        width: '100%',
        boxSizing: 'border-box',
      }}>
        {/* Instrument Status Pill */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.35rem 0.9rem',
          borderRadius: '9999px',
          backgroundColor: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          color: 'var(--accent-cyan)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          letterSpacing: '0.08em',
          marginBottom: '1.5rem',
          boxShadow: '0 0 20px rgba(56, 189, 248, 0.12)',
        }}>
          <Compass size={14} className="animate-spin-slow" />
          <span>NEREUS • SCIENTIFIC OCEAN OBSERVATORY</span>
        </div>

        {/* Hero Title */}
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(2.4rem, 5.5vw, 4rem)',
          fontWeight: 700,
          textAlign: 'center',
          lineHeight: 1.12,
          letterSpacing: '-0.03em',
          maxWidth: '920px',
          margin: '0 0 1.25rem',
          background: 'linear-gradient(180deg, #ffffff 30%, #94a3b8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          Scientific Ocean Exploration
        </h1>

        {/* Core Subtitle: SPACE • TIME • DEPTH */}
        <p style={{
          fontSize: 'clamp(1.05rem, 2vw, 1.35rem)',
          color: 'var(--text-secondary)',
          textAlign: 'center',
          maxWidth: '720px',
          lineHeight: 1.55,
          margin: '0 0 0.75rem',
          fontWeight: 400,
        }}>
          Explore real oceanographic data across:
        </p>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: 'clamp(0.95rem, 1.8vw, 1.2rem)',
          fontFamily: 'var(--font-mono)',
          color: 'var(--accent-cyan)',
          fontWeight: 600,
          letterSpacing: '0.12em',
          marginBottom: '2.25rem',
        }}>
          <span>SPACE</span>
          <span style={{ color: 'var(--border-focus)', opacity: 0.6 }}>•</span>
          <span>TIME</span>
          <span style={{ color: 'var(--border-focus)', opacity: 0.6 }}>•</span>
          <span>DEPTH</span>
        </div>

        {/* Primary & Secondary Call to Actions */}
        <div style={{
          display: 'flex',
          gap: '1rem',
          flexWrap: 'wrap',
          justifyContent: 'center',
          marginBottom: '3.75rem',
        }}>
          <Link
            to="/workspace"
            className="btn-primary-glow"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.6rem',
              padding: '0.9rem 2rem',
              backgroundColor: 'var(--accent-cyan)',
              color: '#030712',
              fontWeight: 600,
              fontSize: '1rem',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
              boxShadow: '0 0 30px rgba(56, 189, 248, 0.35)',
              transition: 'all 0.2s ease',
            }}
          >
            <span>Explore Ocean Data</span>
            <ArrowRight size={18} />
          </Link>

          <Link
            to="/datasets"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.6rem',
              padding: '0.9rem 1.75rem',
              backgroundColor: 'rgba(15, 23, 42, 0.85)',
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

        {/* 3-Step Simple Workflow Explanation */}
        <div style={{
          width: '100%',
          maxWidth: '1080px',
          marginBottom: '3.5rem',
        }}>
          <div style={{
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            textAlign: 'center',
            letterSpacing: '0.08em',
            marginBottom: '1rem',
          }}>
            HOW NEREUS WORKS
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1.25rem',
          }}>
            {/* Step 1 */}
            <div style={{
              backgroundColor: 'rgba(14, 22, 41, 0.75)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '1.5rem',
              backdropFilter: 'blur(10px)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  color: 'var(--accent-cyan)',
                  padding: '0.15rem 0.5rem',
                  backgroundColor: 'rgba(56, 189, 248, 0.1)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                }}>
                  01
                </span>
                <Database size={18} color="var(--accent-cyan)" />
              </div>
              <h3 style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.15rem',
                fontWeight: 600,
                color: 'var(--text-primary)',
                margin: 0,
              }}>
                Choose a dataset
              </h3>
              <p style={{
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
                lineHeight: 1.5,
                margin: 0,
              }}>
                Select from verified Copernicus and satellite oceanographic datasets covering regional seas, temperature, salinity, and current fields.
              </p>
            </div>

            {/* Step 2 */}
            <div style={{
              backgroundColor: 'rgba(14, 22, 41, 0.75)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '1.5rem',
              backdropFilter: 'blur(10px)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  color: 'var(--accent-emerald)',
                  padding: '0.15rem 0.5rem',
                  backgroundColor: 'rgba(16, 185, 129, 0.1)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                }}>
                  02
                </span>
                <SlidersHorizontal size={18} color="var(--accent-emerald)" />
              </div>
              <h3 style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.15rem',
                fontWeight: 600,
                color: 'var(--text-primary)',
                margin: 0,
              }}>
                Explore the ocean
              </h3>
              <p style={{
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
                lineHeight: 1.5,
                margin: 0,
              }}>
                Seamlessly adjust time steps, descend through water-column depth levels, and pan across interactive high-resolution spatial maps.
              </p>
            </div>

            {/* Step 3 */}
            <div style={{
              backgroundColor: 'rgba(14, 22, 41, 0.75)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '1.5rem',
              backdropFilter: 'blur(10px)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  color: 'var(--accent-amber)',
                  padding: '0.15rem 0.5rem',
                  backgroundColor: 'rgba(245, 158, 11, 0.1)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(245, 158, 11, 0.2)',
                }}>
                  03
                </span>
                <LineChart size={18} color="var(--accent-amber)" />
              </div>
              <h3 style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.15rem',
                fontWeight: 600,
                color: 'var(--text-primary)',
                margin: 0,
              }}>
                Analyze the science
              </h3>
              <p style={{
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
                lineHeight: 1.5,
                margin: 0,
              }}>
                Probe vertical depth soundings, inspect hydrodynamic current vectors, correlate multi-variables, and evaluate statistical distributions.
              </p>
            </div>
          </div>
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
              Perceptually uniform colormaps with interactive coordinates probe and decimated Level-of-Detail delivery.
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
              4D Depth Soundings
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
              Vertical water-column profiles, thermocline gradients, and great-circle transect cross-sections.
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
              Time-Series & Climatology
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
              Synchronized temporal playback, station sensor time-series, and baseline anomaly detection.
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
              Integrated U/V vector fields, speed cutoff filters, and directional rose distribution analysis.
            </p>
          </div>
        </div>

        {/* Scientific Pipeline Standards */}
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
            <span>Real Copernicus Ocean Data</span>
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
        <div>NEREUS-SIH • Scientific Ocean Data Exploration</div>
        <div>CF-1.8 Compliant • Real Oceanographic Observations</div>
      </footer>
    </div>
  );
};
