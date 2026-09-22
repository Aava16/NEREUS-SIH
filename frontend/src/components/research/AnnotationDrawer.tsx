import React, { useState } from 'react';
import { 
  MessageSquarePlus, 
  X, 
  Trash2, 
  MapPin, 
  Clock, 
  Plus, 
  Download, 
  Navigation 
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';
import { exportObjectAsJson, downloadBlob } from '../../utils/exportUtils';

export const AnnotationDrawer: React.FC = () => {
  const {
    isAnnotationDrawerOpen,
    setIsAnnotationDrawerOpen,
    annotations,
    addAnnotation,
    deleteAnnotationById,
    datasetId,
    metadata,
    primaryVariable,
    probeLat,
    probeLon,
    timeIndex,
    depthIndex,
    setProbeCoords,
    setTimeIndex,
    setDepthIndex,
    setPrimaryVariable,
    statistics,
  } = useAnalysis();

  const [titleInput, setTitleInput] = useState('');
  const [noteInput, setNoteInput] = useState('');
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isAnnotationDrawerOpen) return null;

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!titleInput.trim()) return;

    addAnnotation({
      title: titleInput.trim(),
      note: noteInput.trim(),
      latitude: probeLat ?? 0,
      longitude: probeLon ?? 0,
      timeIndex,
      depthIndex,
      variable: primaryVariable || 'Unspecified',
      observedValue: statistics?.mean ?? null,
      units: statistics?.units ?? '',
      datasetId: datasetId || 'Unspecified',
      datasetName: metadata?.name || 'Dataset',
    });

    setTitleInput('');
    setNoteInput('');
    setSuccessMsg('Annotation recorded.');
    setTimeout(() => setSuccessMsg(null), 2500);
  };

  const handleExportCsv = () => {
    const lines = [
      'id,title,note,latitude,longitude,variable,observed_value,units,dataset_id,dataset_name,created_at',
      ...annotations.map((a) =>
        `"${a.id}","${a.title.replace(/"/g, '""')}","${a.note.replace(/"/g, '""')}",${a.latitude},${a.longitude},"${a.variable}",${a.observedValue ?? ''},"${a.units || ''}","${a.datasetId}","${a.datasetName || ''}","${a.createdAt}"`
      ),
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    downloadBlob(blob, `nereus_scientific_annotations_${new Date().toISOString().split('T')[0]}.csv`);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      bottom: 0,
      width: '380px',
      maxWidth: '100vw',
      backgroundColor: 'var(--bg-deep)',
      borderLeft: '1px solid var(--border-default)',
      boxShadow: '-10px 0 30px rgba(0, 0, 0, 0.5)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Drawer Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '1rem',
        borderBottom: '1px solid var(--border-subtle)',
        backgroundColor: 'var(--bg-surface)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <MessageSquarePlus size={18} className="text-accent-cyan" />
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            Scientific Annotations
          </h2>
        </div>
        <button
          onClick={() => setIsAnnotationDrawerOpen(false)}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '0.25rem' }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Drawer Body */}
      <div style={{ flex: 1, padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {/* New Annotation Card */}
        <form onSubmit={handleCreate} style={{
          padding: '0.875rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.625rem',
        }}>
          <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 600 }}>
            RECORD OBSERVATION
          </div>

          <div style={{
            fontSize: '0.6875rem',
            fontFamily: 'var(--font-mono)',
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            padding: '0.375rem 0.5rem',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-muted)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.2rem',
          }}>
            <div>Target: <span style={{ color: 'var(--text-primary)' }}>{probeLat !== null && probeLon !== null ? `${probeLat.toFixed(2)}°N, ${probeLon.toFixed(2)}°E` : 'Global/Unset'}</span></div>
            <div>Variable: <span style={{ color: 'var(--accent-emerald)' }}>{primaryVariable || 'None'}</span> | Time: Step {timeIndex + 1} | Depth: Level {depthIndex + 1}</div>
          </div>

          <input
            type="text"
            placeholder="Annotation Title (e.g. Upwelling Front Signature)"
            value={titleInput}
            onChange={(e) => setTitleInput(e.target.value)}
            required
            style={{
              padding: '0.4rem 0.5rem',
              backgroundColor: 'var(--bg-deep)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-primary)',
              fontSize: '0.75rem',
            }}
          />

          <textarea
            placeholder="Detailed scientific observation, anomaly context, or field notes..."
            rows={3}
            value={noteInput}
            onChange={(e) => setNoteInput(e.target.value)}
            style={{
              padding: '0.4rem 0.5rem',
              backgroundColor: 'var(--bg-deep)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-primary)',
              fontSize: '0.75rem',
              resize: 'vertical',
            }}
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {successMsg && (
              <span style={{ fontSize: '0.6875rem', color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)' }}>
                ✓ {successMsg}
              </span>
            )}
            <button
              type="submit"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
                padding: '0.35rem 0.75rem',
                backgroundColor: 'var(--accent-blue)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.6875rem',
                fontWeight: 600,
                cursor: 'pointer',
                marginLeft: 'auto',
              }}
            >
              <Plus size={12} /> Add Annotation
            </button>
          </div>
        </form>

        {/* Existing Annotations List */}
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '0.5rem',
          }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontWeight: 600 }}>
              RECORDED ANNOTATIONS ({annotations.length})
            </span>
            <div style={{ display: 'flex', gap: '0.25rem' }}>
              <button
                onClick={handleExportCsv}
                disabled={annotations.length === 0}
                title="Export annotations as CSV"
                style={{
                  padding: '0.2rem 0.35rem',
                  fontSize: '0.625rem',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-muted)',
                  cursor: annotations.length > 0 ? 'pointer' : 'not-allowed',
                }}
              >
                <Download size={10} /> CSV
              </button>
              <button
                onClick={() => exportObjectAsJson(annotations, 'nereus_annotations.json')}
                disabled={annotations.length === 0}
                title="Export annotations as JSON"
                style={{
                  padding: '0.2rem 0.35rem',
                  fontSize: '0.625rem',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-muted)',
                  cursor: annotations.length > 0 ? 'pointer' : 'not-allowed',
                }}
              >
                JSON
              </button>
            </div>
          </div>

          {annotations.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '1.5rem',
              color: 'var(--text-muted)',
              fontSize: '0.75rem',
              backgroundColor: 'rgba(0, 0, 0, 0.2)',
              borderRadius: 'var(--radius-sm)',
            }}>
              No scientific annotations recorded. Click on a map coordinate and record field notes above.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {annotations.map((a) => (
                <div
                  key={a.id}
                  style={{
                    padding: '0.625rem',
                    backgroundColor: 'var(--bg-surface)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.35rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <strong style={{ fontSize: '0.8125rem', color: 'var(--text-primary)' }}>{a.title}</strong>
                    <button
                      onClick={() => deleteAnnotationById(a.id)}
                      style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '0.125rem' }}
                      title="Delete annotation"
                    >
                      <Trash2 size={12} className="hover:text-accent-rose" />
                    </button>
                  </div>

                  {a.note && (
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
                      {a.note}
                    </p>
                  )}

                  <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                    fontSize: '0.6875rem',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-muted)',
                    borderTop: '1px solid var(--border-subtle)',
                    paddingTop: '0.35rem',
                    marginTop: '0.25rem',
                  }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                      <MapPin size={10} className="text-accent-cyan" /> {a.latitude.toFixed(2)}°N, {a.longitude.toFixed(2)}°E
                    </span>
                    <span>Var: <strong style={{ color: 'var(--accent-emerald)' }}>{a.variable}</strong></span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                      <Clock size={10} /> {a.createdAt.split('T')[0]}
                    </span>
                  </div>

                  <button
                    onClick={() => {
                      setProbeCoords(a.latitude, a.longitude);
                      if (a.timeIndex !== undefined) setTimeIndex(a.timeIndex);
                      if (a.depthIndex !== undefined) setDepthIndex(a.depthIndex);
                      if (a.variable) setPrimaryVariable(a.variable);
                    }}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.25rem',
                      padding: '0.25rem 0',
                      backgroundColor: 'rgba(56, 189, 248, 0.1)',
                      border: '1px solid rgba(56, 189, 248, 0.2)',
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--accent-cyan)',
                      fontSize: '0.6875rem',
                      fontFamily: 'var(--font-mono)',
                      cursor: 'pointer',
                      marginTop: '0.25rem',
                    }}
                  >
                    <Navigation size={10} /> Jump to Location & State
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
