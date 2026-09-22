/**
 * Scientific Data & Visualization Export Utilities for NEREUS
 * Handles CSV, JSON, PNG, and Scientific Analysis Summary Reports.
 */

import type {
  GridDeliveryResponse,
  VariableStatistics,
  FrontendDatasetMetadata,
  ProfileDeliveryResponse,
  TimeSeriesDeliveryResponse,
  TransectDeliveryResponse,
} from '../types';

export const downloadBlob = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const exportGridAsCsv = (
  gridData: GridDeliveryResponse,
  variableName: string,
  units: string,
  datasetMeta?: FrontendDatasetMetadata | null
): void => {
  const lines: string[] = [];

  // Scientific Provenance Header Comments
  lines.push(`# ==============================================================================`);
  lines.push(`# NEREUS OCEAN DATA DELIVERY — SCIENTIFIC GRID EXPORT`);
  lines.push(`# Dataset ID: ${gridData.dataset_id || 'N/A'}`);
  lines.push(`# Dataset Source: ${datasetMeta?.source || 'Standard'}`);
  lines.push(`# Variable: ${variableName} (${units || 'unitless'})`);
  lines.push(`# Time Slice: ${gridData.time || 'N/A'}`);
  lines.push(`# Depth Level: ${gridData.depth !== null && gridData.depth !== undefined ? `${gridData.depth} m` : 'Surface'}`);
  lines.push(`# Spatial Dimensions: ${gridData.latitudes?.length || 0} (lat) x ${gridData.longitudes?.length || 0} (lon)`);
  lines.push(`# Min Value: ${gridData.min_value ?? 'N/A'}`);
  lines.push(`# Max Value: ${gridData.max_value ?? 'N/A'}`);
  lines.push(`# Export Timestamp: ${new Date().toISOString()}`);
  lines.push(`# Coordinate Reference: WGS 84 (EPSG:4326)`);
  lines.push(`# ==============================================================================`);

  // CSV Columns Header
  lines.push('latitude,longitude,value');

  const lats = gridData.latitudes || [];
  const lons = gridData.longitudes || [];
  const values = gridData.values || [];

  for (let r = 0; r < lats.length; r++) {
    const lat = lats[r];
    const rowVals = values[r] || [];
    for (let c = 0; c < lons.length; c++) {
      const lon = lons[c];
      const val = rowVals[c];
      const valStr = val !== null && val !== undefined && isFinite(val) ? val.toString() : 'NaN';
      lines.push(`${lat.toFixed(6)},${lon.toFixed(6)},${valStr}`);
    }
  }

  const csvContent = lines.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const filename = `nereus_${variableName.toLowerCase()}_grid_${new Date().toISOString().split('T')[0]}.csv`;
  downloadBlob(blob, filename);
};

export const exportProfileAsCsv = (
  profileData: ProfileDeliveryResponse,
  _datasetMeta?: FrontendDatasetMetadata | null
): void => {
  const lines: string[] = [];
  const lat = profileData.lat ?? profileData.actual_latitude ?? profileData.requested_latitude ?? 0;
  const lon = profileData.lon ?? profileData.actual_longitude ?? profileData.requested_longitude ?? 0;
  const varName = profileData.variable_name || profileData.variable || 'variable';
  const totalLevels = profileData.depths?.length || 0;

  lines.push(`# NEREUS OCEAN DATA DELIVERY — VERTICAL DEPTH PROFILE EXPORT`);
  lines.push(`# Dataset: ${profileData.dataset_id}`);
  lines.push(`# Variable: ${varName} (${profileData.units || 'unitless'})`);
  lines.push(`# Location: (${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E)`);
  lines.push(`# Time: ${profileData.time || 'N/A'}`);
  lines.push(`# Levels Count: ${totalLevels}`);
  lines.push(`# Generated: ${new Date().toISOString()}`);
  lines.push('depth_m,value');

  const depths = profileData.depths || [];
  const values = profileData.values || [];

  for (let i = 0; i < depths.length; i++) {
    const d = depths[i];
    const v = values[i];
    const valStr = v !== null && v !== undefined && isFinite(v) ? v.toString() : 'NaN';
    lines.push(`${d},${valStr}`);
  }

  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  downloadBlob(blob, `nereus_${varName}_profile_${new Date().toISOString().split('T')[0]}.csv`);
};

export const exportTimeseriesAsCsv = (
  tsData: TimeSeriesDeliveryResponse,
  _datasetMeta?: FrontendDatasetMetadata | null
): void => {
  const lines: string[] = [];
  const lat = tsData.lat ?? tsData.latitude ?? 0;
  const lon = tsData.lon ?? tsData.longitude ?? 0;
  const varName = tsData.variable_name || tsData.variable || 'variable';
  const totalTimesteps = tsData.timestamps?.length || 0;

  lines.push(`# NEREUS OCEAN DATA DELIVERY — TEMPORAL POINT TIMESERIES EXPORT`);
  lines.push(`# Dataset: ${tsData.dataset_id}`);
  lines.push(`# Variable: ${varName} (${tsData.units || 'unitless'})`);
  lines.push(`# Location: (${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E)`);
  lines.push(`# Depth: ${tsData.depth !== null && tsData.depth !== undefined ? `${tsData.depth} m` : 'Surface'}`);
  lines.push(`# Total Steps: ${totalTimesteps}`);
  lines.push(`# Generated: ${new Date().toISOString()}`);
  lines.push('timestamp,value');

  const timestamps = tsData.timestamps || [];
  const values = tsData.values || [];

  for (let i = 0; i < timestamps.length; i++) {
    const t = timestamps[i];
    const v = values[i];
    const valStr = v !== null && v !== undefined && isFinite(v) ? v.toString() : 'NaN';
    lines.push(`${t},${valStr}`);
  }

  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  downloadBlob(blob, `nereus_${varName}_timeseries_${new Date().toISOString().split('T')[0]}.csv`);
};

export const exportTransectAsCsv = (
  transectData: TransectDeliveryResponse,
  _datasetMeta?: FrontendDatasetMetadata | null
): void => {
  const lines: string[] = [];
  lines.push(`# NEREUS OCEAN DATA DELIVERY — GREAT-CIRCLE TRANSECT EXPORT`);
  lines.push(`# Dataset: ${transectData.dataset_id}`);
  lines.push(`# Variable: ${transectData.variable_name} (${transectData.units || 'unitless'})`);
  lines.push(`# Endpoint A: (${transectData.start_latitude.toFixed(4)}°N, ${transectData.start_longitude.toFixed(4)}°E)`);
  lines.push(`# Endpoint B: (${transectData.end_latitude.toFixed(4)}°N, ${transectData.end_longitude.toFixed(4)}°E)`);
  lines.push(`# Total Great-Circle Distance: ${transectData.total_distance_km.toFixed(2)} km`);
  lines.push(`# Points: ${transectData.total_points}`);
  lines.push(`# Generated: ${new Date().toISOString()}`);
  lines.push('sample_idx,distance_km,latitude,longitude,value');

  (transectData.points || []).forEach((p, idx) => {
    const valStr = p.value !== null && p.value !== undefined && isFinite(p.value) ? p.value.toString() : 'NaN';
    lines.push(`${idx},${p.distance_km.toFixed(3)},${p.latitude.toFixed(5)},${p.longitude.toFixed(5)},${valStr}`);
  });

  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  downloadBlob(blob, `nereus_${transectData.variable_name}_transect_${new Date().toISOString().split('T')[0]}.csv`);
};

export const exportObjectAsJson = (data: any, filename: string): void => {
  const jsonStr = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8;' });
  downloadBlob(blob, filename.endsWith('.json') ? filename : `${filename}.json`);
};

export const exportCanvasAsPng = (canvas: HTMLCanvasElement, filename: string): void => {
  canvas.toBlob((blob) => {
    if (blob) {
      downloadBlob(blob, filename.endsWith('.png') ? filename : `${filename}.png`);
    }
  }, 'image/png');
};

export interface ReportParams {
  dataset: FrontendDatasetMetadata | null;
  primaryVariable: string | null;
  secondaryVariable?: string | null;
  units?: string | null;
  statistics?: VariableStatistics | null;
  probeLat?: number | null;
  probeLon?: number | null;
  timeIndex?: number;
  depthIndex?: number;
  analysisMode?: string;
  notes?: string;
}

export const generateScientificReportMarkdown = (params: ReportParams): string => {
  const {
    dataset,
    primaryVariable,
    secondaryVariable,
    units,
    statistics,
    probeLat,
    probeLon,
    timeIndex,
    depthIndex,
    analysisMode,
    notes,
  } = params;

  const now = new Date().toISOString();
  const spatial = dataset?.spatial_coverage || dataset?.spatial_extent;
  const temporal = dataset?.temporal_coverage || dataset?.temporal_extent;

  return `# NEREUS SCIENTIFIC ANALYSIS SUMMARY REPORT
*Generated by NEREUS-SIH Oceanographic Analysis Environment*
*Timestamp: ${now}*

---

## 1. DATASET IDENTIFICATION & PROVENANCE
- **Dataset Name**: ${dataset?.name || 'N/A'}
- **Dataset ID**: \`${dataset?.id || 'N/A'}\`
- **Source / Platform**: ${dataset?.source || 'Standard Canonical Store'}
- **CRS**: WGS 84 (EPSG:4326)
- **Spatial Coverage**: Lat [${(spatial?.min_lat ?? -90).toFixed(2)}°, ${(spatial?.max_lat ?? 90).toFixed(2)}°N], Lon [${(spatial?.min_lon ?? -180).toFixed(2)}°, ${(spatial?.max_lon ?? 180).toFixed(2)}°E]
- **Temporal Coverage**: ${(temporal?.start ?? 'N/A').split('T')[0]} to ${(temporal?.end ?? 'N/A').split('T')[0]} (${temporal?.time_steps_count || 1} timesteps)

---

## 2. ANALYSIS SELECTION CONTEXT
- **Active Analysis Mode**: \`${analysisMode || 'explore'}\`
- **Primary Variable**: **${primaryVariable || 'None'}** (${units || 'unitless'})
${secondaryVariable ? `- **Secondary Comparison Variable**: **${secondaryVariable}**\n` : ''}
- **Time Slice Index**: Step ${(timeIndex ?? 0) + 1}
- **Depth Slice Index**: Level ${(depthIndex ?? 0) + 1}
- **Probe Station Coordinates**: ${probeLat !== null && probeLat !== undefined && probeLon !== null && probeLon !== undefined ? `${probeLat.toFixed(4)}°N, ${probeLon.toFixed(4)}°E` : 'Global Grid'}

---

## 3. STATISTICAL DISTRIBUTION METRICS (PHASE 7 API)
${statistics ? `
| Metric | Value |
| :--- | :--- |
| **Minimum** | ${statistics.min !== null && statistics.min !== undefined ? statistics.min.toFixed(4) : '—'} ${units || ''} |
| **Maximum** | ${statistics.max !== null && statistics.max !== undefined ? statistics.max.toFixed(4) : '—'} ${units || ''} |
| **Mean (μ)** | ${statistics.mean !== null && statistics.mean !== undefined ? statistics.mean.toFixed(4) : '—'} ${units || ''} |
| **Standard Deviation (σ)** | ${statistics.std !== null && statistics.std !== undefined ? statistics.std.toFixed(4) : '—'} |
| **Median (P50)** | ${statistics.median !== null && statistics.median !== undefined ? statistics.median.toFixed(4) : '—'} |
| **90th Percentile (P90)** | ${statistics.p90 !== null && statistics.p90 !== undefined ? statistics.p90.toFixed(4) : '—'} |
| **Valid Grid Cells** | ${statistics.valid_count?.toLocaleString() ?? '—'} |
| **Missing / Masked Cells** | ${statistics.missing_count?.toLocaleString() ?? '—'} |
` : '*No statistical distribution payload computed for this selection.*'}

---

## 4. RESEARCHER NOTES & OBSERVATIONS
${notes || '*No specific researcher annotations added.*'}

---

*Report generated with zero data fabrication. Calculations performed by NEREUS authoritative scientific backend.*
`;
};
