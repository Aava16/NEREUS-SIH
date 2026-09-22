import React, { useState } from 'react';
import { 
  Bookmark, 
  X, 
  Plus, 
  Trash2, 
  Edit2, 
  Play, 
  Download, 
  Upload, 
  Check, 
  Clock 
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';
import { exportObjectAsJson } from '../../utils/exportUtils';
import { saveSnapshot } from '../../utils/storageUtils';
import type { ScientificSnapshot } from '../../types';

export const SnapshotModal: React.FC = () => {
  const {
    isSnapshotModalOpen,
    setIsSnapshotModalOpen,
    snapshots,
    saveCurrentSnapshot,
    loadSnapshot,
    deleteSnapshotById,
    renameSnapshotById,
    datasetId,
    primaryVariable,
    metadata,
  } = useAnalysis();

  const [nameInput, setNameInput] = useState('');
  const [descInput, setDescInput] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isSnapshotModalOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nameInput.trim()) return;
    saveCurrentSnapshot(nameInput.trim(), descInput.trim() || undefined);
    setNameInput('');
    setDescInput('');
    setSuccessMsg('Snapshot saved successfully!');
    setTimeout(() => setSuccessMsg(null), 3000);
  };

  const handleStartRename = (snap: ScientificSnapshot) => {
    setEditingId(snap.id);
    setEditName(snap.name);
  };

  const handleSaveRename = (id: string) => {
    if (editName.trim()) {
      renameSnapshotById(id, editName.trim());
    }
    setEditingId(null);
  };

  const handleExportAll = () => {
    exportObjectAsJson(snapshots, `nereus_analysis_snapshots_${new Date().toISOString().split('T')[0]}.json`);
  };

  const handleImportFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const parsed = JSON.parse(ev.target?.result as string);
        if (Array.isArray(parsed)) {
          parsed.forEach((s) => {
            if (s.id && s.name && s.datasetId) {
              // Save each snapshot
              saveSnapshot(s);
            }
          });
          window.location.reload();
        }
      } catch (err) {
        alert('Invalid snapshots JSON file format.');
      }
    };
    reader.readAsText(file);
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(3, 7, 18, 0.75)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '680px',
        backgroundColor: 'var(--bg-deep)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
        display: 'flex',
        flexDirection: 'column',
        maxHeight: '85vh',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '1rem 1.25rem',
          borderBottom: '1px solid var(--border-subtle)',
          backgroundColor: 'var(--bg-surface)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Bookmark size={18} className="text-accent-cyan" />
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              Scientific Analysis Snapshots
            </h2>
          </div>
          <button
            onClick={() => setIsSnapshotModalOpen(false)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '0.25rem',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '1.25rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Create Snapshot Form */}
          <form onSubmit={handleSave} style={{
            padding: '1rem',
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}>
            <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 600 }}>
              SAVE CURRENT WORKSPACE CONFIGURATION
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              Captures active dataset (<strong>{metadata?.name || datasetId || 'None'}</strong>), variable (<strong>{primaryVariable || 'None'}</strong>), time, depth, and analysis mode.
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <input
                type="text"
                placeholder="Snapshot Name (e.g. Arabian Sea SST Anomaly)"
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                required
                style={{
                  padding: '0.5rem 0.625rem',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)',
                  fontSize: '0.8125rem',
                }}
              />
              <input
                type="text"
                placeholder="Optional description / notes"
                value={descInput}
                onChange={(e) => setDescInput(e.target.value)}
                style={{
                  padding: '0.5rem 0.625rem',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)',
                  fontSize: '0.8125rem',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              {successMsg && (
                <span style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)' }}>
                  ✓ {successMsg}
                </span>
              )}
              <button
                type="submit"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.375rem',
                  padding: '0.4rem 0.875rem',
                  backgroundColor: 'var(--accent-blue)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  marginLeft: 'auto',
                }}
              >
                <Plus size={14} /> Save Snapshot
              </button>
            </div>
          </form>

          {/* Saved Snapshots List */}
          <div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '0.625rem',
            }}>
              <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontWeight: 600 }}>
                SAVED SNAPSHOTS ({snapshots.length})
              </span>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  type="button"
                  onClick={handleExportAll}
                  disabled={snapshots.length === 0}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    padding: '0.25rem 0.5rem',
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.6875rem',
                    color: 'var(--text-secondary)',
                    cursor: snapshots.length > 0 ? 'pointer' : 'not-allowed',
                  }}
                >
                  <Download size={12} /> Export JSON
                </button>
                <label style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  padding: '0.25rem 0.5rem',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.6875rem',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                }}>
                  <Upload size={12} /> Import
                  <input type="file" accept=".json" onChange={handleImportFile} style={{ display: 'none' }} />
                </label>
              </div>
            </div>

            {snapshots.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '2rem',
                backgroundColor: 'rgba(0, 0, 0, 0.2)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-muted)',
                fontSize: '0.8125rem',
              }}>
                No saved snapshots. Save the current analysis view above to revisit or share configurations.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {snapshots.map((s) => (
                  <div
                    key={s.id}
                    style={{
                      padding: '0.75rem',
                      backgroundColor: 'var(--bg-surface)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '0.75rem',
                    }}
                  >
                    <div style={{ flex: 1, minWidth: 0 }}>
                      {editingId === s.id ? (
                        <div style={{ display: 'flex', gap: '0.375rem', alignItems: 'center' }}>
                          <input
                            type="text"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            style={{
                              padding: '0.25rem 0.5rem',
                              backgroundColor: 'var(--bg-deep)',
                              border: '1px solid var(--border-focus)',
                              borderRadius: 'var(--radius-sm)',
                              color: 'var(--text-primary)',
                              fontSize: '0.8125rem',
                            }}
                          />
                          <button
                            onClick={() => handleSaveRename(s.id)}
                            style={{ padding: '0.25rem', background: 'none', border: 'none', color: 'var(--accent-emerald)', cursor: 'pointer' }}
                          >
                            <Check size={16} />
                          </button>
                        </div>
                      ) : (
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.8125rem' }}>
                          {s.name}
                        </div>
                      )}
                      {s.description && (
                        <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.125rem' }}>
                          {s.description}
                        </div>
                      )}
                      <div style={{
                        display: 'flex',
                        gap: '0.75rem',
                        fontSize: '0.6875rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--text-muted)',
                        marginTop: '0.25rem',
                      }}>
                        <span>Dataset: <span style={{ color: 'var(--accent-cyan)' }}>{s.datasetName || s.datasetId}</span></span>
                        <span>Var: <span style={{ color: 'var(--text-secondary)' }}>{s.primaryVariable || 'None'}</span></span>
                        <span>Mode: <span style={{ color: 'var(--text-secondary)' }}>{s.analysisMode}</span></span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                          <Clock size={10} /> {s.timestamp.split('T')[0]}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                      <button
                        onClick={() => {
                          loadSnapshot(s);
                          setIsSnapshotModalOpen(false);
                        }}
                        title="Load this snapshot into workspace"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          padding: '0.35rem 0.625rem',
                          backgroundColor: 'rgba(56, 189, 248, 0.15)',
                          border: '1px solid var(--border-focus)',
                          borderRadius: 'var(--radius-sm)',
                          color: 'var(--accent-cyan)',
                          fontSize: '0.6875rem',
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        <Play size={11} /> Load
                      </button>
                      <button
                        onClick={() => handleStartRename(s)}
                        title="Rename snapshot"
                        style={{
                          padding: '0.35rem',
                          backgroundColor: 'transparent',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-sm)',
                          color: 'var(--text-muted)',
                          cursor: 'pointer',
                        }}
                      >
                        <Edit2 size={12} />
                      </button>
                      <button
                        onClick={() => deleteSnapshotById(s.id)}
                        title="Delete snapshot"
                        style={{
                          padding: '0.35rem',
                          backgroundColor: 'transparent',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-sm)',
                          color: 'var(--accent-rose)',
                          cursor: 'pointer',
                        }}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
