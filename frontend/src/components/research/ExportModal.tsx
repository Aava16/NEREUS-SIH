import React, { useState } from 'react';
import { 
  Download, 
  X, 
  FileSpreadsheet, 
  FileCode, 
  FileText, 
  Image, 
  CheckCircle2 
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';
import {
  exportGridAsCsv,
  exportProfileAsCsv,
  exportTimeseriesAsCsv,
  exportTransectAsCsv,
  exportObjectAsJson,
  exportCanvasAsPng,
  generateScientificReportMarkdown,
  downloadBlob,
} from '../../utils/exportUtils';
import type { ExportFormat } from '../../types';

export const ExportModal: React.FC = () => {
  const {
    isExportModalOpen,
    setIsExportModalOpen,
    datasetId,
    metadata,
    primaryVariable,
    secondaryVariable,
    gridData,
    profileData,
    timeseriesData,
    transectData,
    statistics,
    probeLat,
    probeLon,
    timeIndex,
    depthIndex,
    analysisMode,
  } = useAnalysis();

  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('csv');
  const [reportNotes, setReportNotes] = useState('');
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  if (!isExportModalOpen) return null;

  const handleExport = () => {
    const varName = primaryVariable || 'variable';
    const units = statistics?.units || '';

    try {
      if (selectedFormat === 'csv') {
        if (analysisMode === 'profile' && profileData) {
          exportProfileAsCsv(profileData, metadata);
        } else if (analysisMode === 'timeseries' && timeseriesData) {
          exportTimeseriesAsCsv(timeseriesData, metadata);
        } else if (analysisMode === 'transect' && transectData) {
          exportTransectAsCsv(transectData, metadata);
        } else if (gridData) {
          exportGridAsCsv(gridData, varName, units, metadata);
        } else {
          alert('No active 2D grid slice to export as CSV.');
          return;
        }
      } else if (selectedFormat === 'json') {
        const payload = {
          dataset_id: datasetId,
          dataset_name: metadata?.name,
          variable: varName,
          units,
          time_index: timeIndex,
          depth_index: depthIndex,
          analysis_mode: analysisMode,
          probe_coordinates: probeLat !== null && probeLon !== null ? { latitude: probeLat, longitude: probeLon } : null,
          statistics,
          grid: gridData ? { latitudes: gridData.latitudes, longitudes: gridData.longitudes, values: gridData.values } : null,
          exported_at: new Date().toISOString(),
        };
        exportObjectAsJson(payload, `nereus_${varName}_analysis_${new Date().toISOString().split('T')[0]}.json`);
      } else if (selectedFormat === 'report') {
        const markdown = generateScientificReportMarkdown({
          dataset: metadata,
          primaryVariable,
          secondaryVariable,
          units,
          statistics,
          probeLat,
          probeLon,
          timeIndex,
          depthIndex,
          analysisMode,
          notes: reportNotes.trim() || undefined,
        });
        const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8;' });
        downloadBlob(blob, `nereus_scientific_report_${varName}_${new Date().toISOString().split('T')[0]}.md`);
      } else if (selectedFormat === 'png') {
        // Find main canvas in DOM
        const canvases = document.querySelectorAll('canvas');
        if (canvases.length > 0) {
          const mainCanvas = canvases[0] as HTMLCanvasElement;
          exportCanvasAsPng(mainCanvas, `nereus_${analysisMode}_visualization_${new Date().toISOString().split('T')[0]}.png`);
        } else {
          alert('No active visual canvas found to export.');
          return;
        }
      }

      setDownloadSuccess(`Export completed (${selectedFormat.toUpperCase()})`);
      setTimeout(() => setDownloadSuccess(null), 3000);
    } catch (err: any) {
      alert(`Export error: ${err.message}`);
    }
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
        maxWidth: '580px',
        backgroundColor: 'var(--bg-deep)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
        display: 'flex',
        flexDirection: 'column',
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
            <Download size={18} className="text-accent-cyan" />
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              Export Scientific Analysis Results
            </h2>
          </div>
          <button
            onClick={() => setIsExportModalOpen(false)}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '0.25rem' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Format Selector Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.625rem' }}>
            <button
              onClick={() => setSelectedFormat('csv')}
              style={{
                padding: '0.75rem',
                backgroundColor: selectedFormat === 'csv' ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-surface)',
                border: selectedFormat === 'csv' ? '1px solid var(--border-focus)' : '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.625rem',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <FileSpreadsheet size={20} className={selectedFormat === 'csv' ? 'text-accent-cyan' : 'text-text-muted'} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: selectedFormat === 'csv' ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                  CSV Tabular Data
                </div>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                  With metadata header & coordinates
                </div>
              </div>
            </button>

            <button
              onClick={() => setSelectedFormat('json')}
              style={{
                padding: '0.75rem',
                backgroundColor: selectedFormat === 'json' ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-surface)',
                border: selectedFormat === 'json' ? '1px solid var(--border-focus)' : '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.625rem',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <FileCode size={20} className={selectedFormat === 'json' ? 'text-accent-cyan' : 'text-text-muted'} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: selectedFormat === 'json' ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                  Structured JSON
                </div>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                  Complete slice & statistics payload
                </div>
              </div>
            </button>

            <button
              onClick={() => setSelectedFormat('report')}
              style={{
                padding: '0.75rem',
                backgroundColor: selectedFormat === 'report' ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-surface)',
                border: selectedFormat === 'report' ? '1px solid var(--border-focus)' : '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.625rem',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <FileText size={20} className={selectedFormat === 'report' ? 'text-accent-cyan' : 'text-text-muted'} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: selectedFormat === 'report' ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                  Analysis Summary Report
                </div>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                  Formatted scientific Markdown
                </div>
              </div>
            </button>

            <button
              onClick={() => setSelectedFormat('png')}
              style={{
                padding: '0.75rem',
                backgroundColor: selectedFormat === 'png' ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-surface)',
                border: selectedFormat === 'png' ? '1px solid var(--border-focus)' : '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.625rem',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <Image size={20} className={selectedFormat === 'png' ? 'text-accent-cyan' : 'text-text-muted'} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: selectedFormat === 'png' ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                  PNG Visualization
                </div>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                  High-res canvas raster capture
                </div>
              </div>
            </button>
          </div>

          {/* Optional Report Notes for Report Format */}
          {selectedFormat === 'report' && (
            <div>
              <label style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', display: 'block', marginBottom: '0.35rem' }}>
                RESEARCHER OBSERVATIONS / INTERPRETATION (OPTIONAL)
              </label>
              <textarea
                placeholder="Include custom experimental context, scientific hypotheses, or anomalies noted..."
                rows={3}
                value={reportNotes}
                onChange={(e) => setReportNotes(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)',
                  fontSize: '0.75rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>
          )}

          {/* Summary Context */}
          <div style={{
            fontSize: '0.6875rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            padding: '0.5rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.2rem',
          }}>
            <div>Dataset: <strong style={{ color: 'var(--text-primary)' }}>{metadata?.name || datasetId || 'None'}</strong></div>
            <div>Variable: <strong style={{ color: 'var(--accent-emerald)' }}>{primaryVariable}</strong> ({statistics?.units || 'unitless'})</div>
            <div>Selection: Time Step {timeIndex + 1} | Depth Level {depthIndex + 1} | Mode: {analysisMode}</div>
          </div>

          {/* Footer Actions */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
            {downloadSuccess ? (
              <span style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '0.25rem', fontFamily: 'var(--font-mono)' }}>
                <CheckCircle2 size={14} /> {downloadSuccess}
              </span>
            ) : (
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                Authoritative backend values will be exported.
              </span>
            )}

            <button
              onClick={handleExport}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.375rem',
                padding: '0.5rem 1.25rem',
                backgroundColor: 'var(--accent-blue)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Download size={14} /> Export File
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
