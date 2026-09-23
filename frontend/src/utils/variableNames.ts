/**
 * Oceanographic Variable Name Humanizer Utility
 * Maps technical CF-1.8 and NetCDF variable codes to clear, human-readable labels
 * while retaining exact scientific identifiers as secondary metadata.
 */

export interface VariableDisplayMeta {
  code: string;
  label: string;
  description: string;
  unitsFallback?: string;
}

const VARIABLE_REGISTRY: Record<string, VariableDisplayMeta> = {
  thetao: {
    code: 'thetao',
    label: 'Temperature',
    description: 'Sea water potential temperature across the water column',
    unitsFallback: '°C',
  },
  temp: {
    code: 'temp',
    label: 'Temperature',
    description: 'Sea water temperature',
    unitsFallback: '°C',
  },
  temperature: {
    code: 'temperature',
    label: 'Temperature',
    description: 'Sea water temperature',
    unitsFallback: '°C',
  },
  sst: {
    code: 'sst',
    label: 'Sea Surface Temperature',
    description: 'Upper ocean skin/bulk surface temperature',
    unitsFallback: '°C',
  },
  so: {
    code: 'so',
    label: 'Salinity',
    description: 'Sea water practical salinity',
    unitsFallback: 'PSU',
  },
  salinity: {
    code: 'salinity',
    label: 'Salinity',
    description: 'Sea water salinity',
    unitsFallback: 'PSU',
  },
  uo: {
    code: 'uo',
    label: 'Eastward Current',
    description: 'Zonal velocity component (positive eastward)',
    unitsFallback: 'm/s',
  },
  u: {
    code: 'u',
    label: 'Eastward Current',
    description: 'Zonal velocity component (positive eastward)',
    unitsFallback: 'm/s',
  },
  vo: {
    code: 'vo',
    label: 'Northward Current',
    description: 'Meridional velocity component (positive northward)',
    unitsFallback: 'm/s',
  },
  v: {
    code: 'v',
    label: 'Northward Current',
    description: 'Meridional velocity component (positive northward)',
    unitsFallback: 'm/s',
  },
  wo: {
    code: 'wo',
    label: 'Vertical Velocity',
    description: 'Upwelling/downwelling vertical velocity',
    unitsFallback: 'm/s',
  },
  w: {
    code: 'w',
    label: 'Vertical Velocity',
    description: 'Upwelling/downwelling vertical velocity',
    unitsFallback: 'm/s',
  },
  zos: {
    code: 'zos',
    label: 'Sea Surface Height',
    description: 'Sea surface height above geoid / sea level anomaly',
    unitsFallback: 'm',
  },
  ssh: {
    code: 'ssh',
    label: 'Sea Surface Height',
    description: 'Sea surface height above reference datum',
    unitsFallback: 'm',
  },
  sla: {
    code: 'sla',
    label: 'Sea Level Anomaly',
    description: 'Deviation of sea level from mean dynamic topography',
    unitsFallback: 'm',
  },
  mlotst: {
    code: 'mlotst',
    label: 'Mixed Layer Depth',
    description: 'Ocean mixed layer thickness defined by density threshold',
    unitsFallback: 'm',
  },
  mld: {
    code: 'mld',
    label: 'Mixed Layer Depth',
    description: 'Ocean mixed layer depth',
    unitsFallback: 'm',
  },
  current_speed: {
    code: 'current_speed',
    label: 'Current Speed',
    description: 'Total horizontal velocity magnitude √(u² + v²)',
    unitsFallback: 'm/s',
  },
  speed: {
    code: 'speed',
    label: 'Current Speed',
    description: 'Velocity magnitude √(u² + v²)',
    unitsFallback: 'm/s',
  },
  chl: {
    code: 'chl',
    label: 'Chlorophyll-a',
    description: 'Mass concentration of chlorophyll-a in sea water',
    unitsFallback: 'mg/m³',
  },
  chlorophyll: {
    code: 'chlorophyll',
    label: 'Chlorophyll-a',
    description: 'Phytoplankton chlorophyll concentration',
    unitsFallback: 'mg/m³',
  },
};

/**
 * Returns a human-friendly display label with scientific code fallback.
 */
export function getVariableDisplay(varName?: string | null): {
  label: string;
  code: string;
  fullTitle: string;
  description?: string;
} {
  if (!varName) {
    return { label: '—', code: '', fullTitle: 'No Variable' };
  }

  const cleanName = varName.trim();
  const lower = cleanName.toLowerCase();
  const entry = VARIABLE_REGISTRY[lower];

  if (entry) {
    return {
      label: entry.label,
      code: cleanName,
      fullTitle: `${entry.label} (${cleanName})`,
      description: entry.description,
    };
  }

  // Fallback: capitalize snake_case / camelCase
  const formatted = cleanName
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .replace(/^\w/, (c) => c.toUpperCase());

  return {
    label: formatted,
    code: cleanName,
    fullTitle: cleanName,
    description: `${formatted} oceanographic variable`,
  };
}

/**
 * Short label for compact buttons/selectors (e.g. "Temperature")
 */
export function getVariableShortLabel(varName?: string | null): string {
  return getVariableDisplay(varName).label;
}
