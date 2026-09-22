import React, { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { listDatasets, getDatasetMetadata, getDatasetVariables } from '../api/datasets';
import { getGrid, getProfile, getTimeseries, getCurrentVectors, getTransect } from '../api/delivery';
import { getStatistics, getCurrentsAnalysis, getDatasetSummary } from '../api/analysis';
import {
  loadSnapshots,
  saveSnapshot,
  deleteSnapshot,
  renameSnapshot,
  loadAnnotations,
  saveAnnotation,
  deleteAnnotation,
} from '../utils/storageUtils';
import type {
  DatasetListItem,
  FrontendDatasetMetadata,
  DatasetVariableInfo,
  GridDeliveryResponse,
  ProfileDeliveryResponse,
  TimeSeriesDeliveryResponse,
  CurrentsDeliveryResponse,
  TransectDeliveryResponse,
  VariableStatistics,
  CurrentsAnalysisResponse,
  DatasetAnalysisSummaryResponse,
  AnalysisMode,
  ColormapName,
  TransectCoords,
  RegionBounds,
  DisplayScaleConfig,
  ScientificSnapshot,
  ScientificAnnotation,
} from '../types';

interface LoadingState {
  datasets: boolean;
  grid: boolean;
  profile: boolean;
  timeseries: boolean;
  transect: boolean;
  stats: boolean;
  currents: boolean;
}

interface AnalysisContextType {
  // Datasets
  datasets: DatasetListItem[];
  datasetId: string | null;
  setDatasetId: (id: string) => void;
  metadata: FrontendDatasetMetadata | null;
  variables: DatasetVariableInfo[];

  // Variables & Slices
  primaryVariable: string | null;
  setPrimaryVariable: (v: string | null) => void;
  secondaryVariable: string | null;
  setSecondaryVariable: (v: string | null) => void;
  timeIndex: number;
  setTimeIndex: (idx: number) => void;
  depthIndex: number;
  setDepthIndex: (idx: number) => void;

  // Spatial Probes, Region Bounds & Transect
  probeLat: number | null;
  probeLon: number | null;
  setProbeCoords: (lat: number, lon: number) => void;
  regionBounds: RegionBounds | null;
  setRegionBounds: (bounds: RegionBounds | null) => void;
  clearRegionBounds: () => void;
  transectCoords: TransectCoords;
  setTransectCoords: React.Dispatch<React.SetStateAction<TransectCoords>>;

  // Modes & Controls
  analysisMode: AnalysisMode;
  setAnalysisMode: (mode: AnalysisMode) => void;
  colormap: ColormapName;
  setColormap: (cm: ColormapName) => void;
  showVectors: boolean;
  setShowVectors: (show: boolean) => void;
  speedThreshold: number;
  setSpeedThreshold: (val: number) => void;
  displayScale: DisplayScaleConfig;
  setDisplayScale: React.Dispatch<React.SetStateAction<DisplayScaleConfig>>;
  resetDisplayScale: () => void;

  // Time Player Controls
  isPlaying: boolean;
  togglePlay: () => void;
  stepForward: () => void;
  stepBackward: () => void;

  // Delivery Data
  gridData: GridDeliveryResponse | null;
  secondaryGridData: GridDeliveryResponse | null;
  profileData: ProfileDeliveryResponse | null;
  timeseriesData: TimeSeriesDeliveryResponse | null;
  vectorData: CurrentsDeliveryResponse | null;
  transectData: TransectDeliveryResponse | null;

  // Analytics Data
  statistics: VariableStatistics | null;
  secondaryStatistics: VariableStatistics | null;
  currentsAnalysis: CurrentsAnalysisResponse | null;
  summaryAnalysis: DatasetAnalysisSummaryResponse | null;

  // Snapshots
  snapshots: ScientificSnapshot[];
  saveCurrentSnapshot: (name: string, description?: string) => void;
  loadSnapshot: (snapshot: ScientificSnapshot) => void;
  deleteSnapshotById: (id: string) => void;
  renameSnapshotById: (id: string, name: string) => void;

  // Annotations
  annotations: ScientificAnnotation[];
  addAnnotation: (data: Omit<ScientificAnnotation, 'id' | 'createdAt'>) => void;
  deleteAnnotationById: (id: string) => void;

  // Modals / Drawers
  isSnapshotModalOpen: boolean;
  setIsSnapshotModalOpen: (open: boolean) => void;
  isAnnotationDrawerOpen: boolean;
  setIsAnnotationDrawerOpen: (open: boolean) => void;
  isProvenanceModalOpen: boolean;
  setIsProvenanceModalOpen: (open: boolean) => void;
  isExportModalOpen: boolean;
  setIsExportModalOpen: (open: boolean) => void;

  // Actions & Lifecycle
  resetWorkspace: () => void;
  loading: LoadingState;
  error: string | null;
  clearError: () => void;
  refreshAll: () => Promise<void>;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export const AnalysisProvider: React.FC<{ children: ReactNode; initialDatasetId?: string }> = ({
  children,
  initialDatasetId,
}) => {
  // Parse initial query params from URL
  const searchParams = new URLSearchParams(window.location.search);
  const urlDatasetId = searchParams.get('dataset') || searchParams.get('id') || initialDatasetId || null;
  const urlVariable = searchParams.get('variable') || null;
  const urlSecondary = searchParams.get('secondary') || null;
  const urlTimeIndex = searchParams.get('time') ? parseInt(searchParams.get('time')!) : 0;
  const urlDepthIndex = searchParams.get('depth') ? parseInt(searchParams.get('depth')!) : 0;
  const urlLat = searchParams.get('lat') ? parseFloat(searchParams.get('lat')!) : null;
  const urlLon = searchParams.get('lon') ? parseFloat(searchParams.get('lon')!) : null;
  const urlMode = (searchParams.get('mode') as AnalysisMode) || 'explore';

  // Dataset & metadata
  const [datasets, setDatasets] = useState<DatasetListItem[]>([]);
  const [datasetId, setDatasetId] = useState<string | null>(urlDatasetId);
  const [metadata, setMetadata] = useState<FrontendDatasetMetadata | null>(null);
  const [variables, setVariables] = useState<DatasetVariableInfo[]>([]);

  // Slices & Variables
  const [primaryVariable, setPrimaryVariable] = useState<string | null>(urlVariable);
  const [secondaryVariable, setSecondaryVariable] = useState<string | null>(urlSecondary);
  const [timeIndex, setTimeIndex] = useState<number>(urlTimeIndex);
  const [depthIndex, setDepthIndex] = useState<number>(urlDepthIndex);

  // Probes & Region Selection
  const [probeLat, setProbeLat] = useState<number | null>(urlLat);
  const [probeLon, setProbeLon] = useState<number | null>(urlLon);
  const [regionBounds, setRegionBounds] = useState<RegionBounds | null>(null);
  const [transectCoords, setTransectCoords] = useState<TransectCoords>({
    lat1: 10.0,
    lon1: 70.0,
    lat2: 18.0,
    lon2: 80.0,
    numPoints: 50,
  });

  // Mode & Visual Settings
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>(urlMode);
  const [colormap, setColormap] = useState<ColormapName>('viridis');
  const [showVectors, setShowVectors] = useState<boolean>(false);
  const [speedThreshold, setSpeedThreshold] = useState<number>(0);
  const [displayScale, setDisplayScale] = useState<DisplayScaleConfig>({ mode: 'auto' });

  // Time Player
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Data Payloads
  const [gridData, setGridData] = useState<GridDeliveryResponse | null>(null);
  const [secondaryGridData, setSecondaryGridData] = useState<GridDeliveryResponse | null>(null);
  const [profileData, setProfileData] = useState<ProfileDeliveryResponse | null>(null);
  const [timeseriesData, setTimeseriesData] = useState<TimeSeriesDeliveryResponse | null>(null);
  const [vectorData, setVectorData] = useState<CurrentsDeliveryResponse | null>(null);
  const [transectData, setTransectData] = useState<TransectDeliveryResponse | null>(null);

  // Analytics Payloads
  const [statistics, setStatistics] = useState<VariableStatistics | null>(null);
  const [secondaryStatistics, setSecondaryStatistics] = useState<VariableStatistics | null>(null);
  const [currentsAnalysis, setCurrentsAnalysis] = useState<CurrentsAnalysisResponse | null>(null);
  const [summaryAnalysis, setSummaryAnalysis] = useState<DatasetAnalysisSummaryResponse | null>(null);

  // Snapshots & Annotations
  const [snapshots, setSnapshots] = useState<ScientificSnapshot[]>(() => loadSnapshots());
  const [annotations, setAnnotations] = useState<ScientificAnnotation[]>(() => loadAnnotations());

  // Modals & Drawers Visibility
  const [isSnapshotModalOpen, setIsSnapshotModalOpen] = useState<boolean>(false);
  const [isAnnotationDrawerOpen, setIsAnnotationDrawerOpen] = useState<boolean>(false);
  const [isProvenanceModalOpen, setIsProvenanceModalOpen] = useState<boolean>(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState<boolean>(false);

  // Loading & Errors
  const [loading, setLoading] = useState<LoadingState>({
    datasets: true,
    grid: false,
    profile: false,
    timeseries: false,
    transect: false,
    stats: false,
    currents: false,
  });
  const [error, setError] = useState<string | null>(null);

  const clearError = () => setError(null);

  const setProbeCoords = (lat: number, lon: number) => {
    setProbeLat(lat);
    setProbeLon(lon);
  };

  const clearRegionBounds = () => setRegionBounds(null);

  const resetDisplayScale = () => setDisplayScale({ mode: 'auto' });

  // 1. Initial Load: Fetch Datasets Catalog
  const fetchDatasets = useCallback(async () => {
    setLoading((prev) => ({ ...prev, datasets: true }));
    setError(null);
    try {
      const res = await listDatasets();
      setDatasets(res.items || []);
      if (!datasetId && res.items && res.items.length > 0) {
        setDatasetId(res.items[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch datasets.');
    } finally {
      setLoading((prev) => ({ ...prev, datasets: false }));
    }
  }, [datasetId]);

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  // 2. Load Dataset Metadata & Variables
  useEffect(() => {
    if (!datasetId) {
      setMetadata(null);
      setVariables([]);
      setPrimaryVariable(null);
      setSecondaryVariable(null);
      return;
    }

    let isMounted = true;
    const loadMetadata = async () => {
      try {
        const [meta, varDiscovery] = await Promise.all([
          getDatasetMetadata(datasetId),
          getDatasetVariables(datasetId),
        ]);
        if (!isMounted) return;

        setMetadata(meta);

        // Enhance variables list with derived tags if U/V exist
        const rawVars = varDiscovery.variables || [];
        const hasU = rawVars.some((v) => ['u', 'uo', 'water_u'].includes((v.name || v.variable_name || '').toLowerCase()));
        const hasV = rawVars.some((v) => ['v', 'vo', 'water_v'].includes((v.name || v.variable_name || '').toLowerCase()));

        const enhancedVars: DatasetVariableInfo[] = [...rawVars];
        if (hasU && hasV) {
          enhancedVars.push({
            name: 'current_speed',
            variable_name: 'current_speed',
            standard_name: 'sea_water_speed',
            long_name: 'Ocean Current Speed Magnitude (derived)',
            units: 'm/s',
            dtype: 'float32',
            is_derived: true,
            dimensions: ['lat', 'lon'],
            shape: [],
          });
        }

        setVariables(enhancedVars);

        // Pick initial variable if not selected or invalid
        if (enhancedVars.length > 0) {
          if (!primaryVariable || !enhancedVars.some((v) => (v.name || v.variable_name) === primaryVariable)) {
            const defaultPrimary = enhancedVars.find((v) => {
              const n = (v.name || v.variable_name || '').toLowerCase();
              return ['temp', 'sst', 'temperature', 'salinity'].includes(n);
            }) || enhancedVars[0];
            setPrimaryVariable(defaultPrimary.name || defaultPrimary.variable_name || null);
          }

          if (!secondaryVariable || !enhancedVars.some((v) => (v.name || v.variable_name) === secondaryVariable)) {
            const defaultSec = enhancedVars.find((v) => (v.name || v.variable_name) !== primaryVariable) || null;
            setSecondaryVariable(defaultSec ? (defaultSec.name || defaultSec.variable_name || null) : null);
          }
        }

        // Initialize probe coordinates from spatial extent if not set
        const spatial = meta.spatial_coverage || meta.spatial_extent;
        if (spatial && spatial.min_lat !== undefined && spatial.max_lat !== undefined) {
          if (probeLat === null) {
            const midLat = (spatial.min_lat + spatial.max_lat) / 2;
            const midLon = ((spatial.min_lon ?? 0) + (spatial.max_lon ?? 0)) / 2;
            setProbeLat(midLat);
            setProbeLon(midLon);
          }
          setTransectCoords({
            lat1: spatial.min_lat,
            lon1: spatial.min_lon ?? 0,
            lat2: spatial.max_lat,
            lon2: spatial.max_lon ?? 0,
            numPoints: 50,
          });
        }
      } catch (err: any) {
        if (isMounted) setError(`Metadata fetch error: ${err.message}`);
      }
    };

    loadMetadata();
    return () => { isMounted = false; };
  }, [datasetId]);

  // 3. Synchronize URL State
  useEffect(() => {
    if (!datasetId) return;
    const params = new URLSearchParams();
    params.set('dataset', datasetId);
    if (primaryVariable) params.set('variable', primaryVariable);
    if (secondaryVariable && analysisMode === 'compare') params.set('secondary', secondaryVariable);
    if (timeIndex > 0) params.set('time', timeIndex.toString());
    if (depthIndex > 0) params.set('depth', depthIndex.toString());
    if (probeLat !== null) params.set('lat', probeLat.toFixed(4));
    if (probeLon !== null) params.set('lon', probeLon.toFixed(4));
    if (analysisMode !== 'explore') params.set('mode', analysisMode);

    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState(null, '', newUrl);
  }, [datasetId, primaryVariable, secondaryVariable, timeIndex, depthIndex, probeLat, probeLon, analysisMode]);

  // 4. Time Player Animation Loop
  useEffect(() => {
    if (!isPlaying) return;
    const maxSteps = metadata?.temporal_coverage?.time_steps_count || metadata?.temporal_extent?.total_timesteps || 1;
    if (maxSteps <= 1) {
      setIsPlaying(false);
      return;
    }

    const interval = setInterval(() => {
      setTimeIndex((prev) => (prev + 1) % maxSteps);
    }, 1500);

    return () => clearInterval(interval);
  }, [isPlaying, metadata]);

  const togglePlay = () => setIsPlaying((prev) => !prev);
  const stepForward = () => {
    const maxSteps = metadata?.temporal_coverage?.time_steps_count || metadata?.temporal_extent?.total_timesteps || 1;
    setTimeIndex((prev) => (prev + 1) % maxSteps);
  };
  const stepBackward = () => {
    const maxSteps = metadata?.temporal_coverage?.time_steps_count || metadata?.temporal_extent?.total_timesteps || 1;
    setTimeIndex((prev) => (prev - 1 + maxSteps) % maxSteps);
  };

  // 5. Fetch Primary 2D Grid and Statistics (Region-Aware)
  useEffect(() => {
    if (!datasetId || !primaryVariable) {
      setGridData(null);
      setStatistics(null);
      return;
    }

    let isMounted = true;
    const timer = setTimeout(async () => {
      setLoading((prev) => ({ ...prev, grid: true, stats: true }));
      clearError();

      try {
        const fetchVar = primaryVariable === 'current_speed' ? 'u' : primaryVariable;
        const gData = await getGrid(datasetId, fetchVar, {
          time_index: timeIndex,
          depth_index: depthIndex,
          min_lat: regionBounds?.minLat,
          max_lat: regionBounds?.maxLat,
          min_lon: regionBounds?.minLon,
          max_lon: regionBounds?.maxLon,
        });
        if (isMounted) setGridData(gData);
      } catch (err: any) {
        if (isMounted) setError(`Grid delivery error (${primaryVariable}): ${err.message}`);
      } finally {
        if (isMounted) setLoading((prev) => ({ ...prev, grid: false }));
      }

      try {
        const statsRes: any = await getStatistics(datasetId, primaryVariable === 'current_speed' ? undefined : primaryVariable);
        if (isMounted) {
          if (statsRes?.variables && statsRes.variables[primaryVariable]) {
            setStatistics(statsRes.variables[primaryVariable]);
          } else if (statsRes?.min !== undefined) {
            setStatistics(statsRes);
          } else {
            setStatistics(null);
          }
        }
      } catch {
        if (isMounted) setStatistics(null);
      } finally {
        if (isMounted) setLoading((prev) => ({ ...prev, stats: false }));
      }
    }, 120);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [datasetId, primaryVariable, timeIndex, depthIndex, regionBounds]);

  // 6. Fetch Secondary Grid & Statistics for Comparison Mode
  useEffect(() => {
    if (!datasetId || !secondaryVariable || analysisMode !== 'compare') {
      setSecondaryGridData(null);
      setSecondaryStatistics(null);
      return;
    }

    let isMounted = true;
    const timer = setTimeout(async () => {
      try {
        const gData = await getGrid(datasetId, secondaryVariable, {
          time_index: timeIndex,
          depth_index: depthIndex,
          min_lat: regionBounds?.minLat,
          max_lat: regionBounds?.maxLat,
          min_lon: regionBounds?.minLon,
          max_lon: regionBounds?.maxLon,
        });
        if (isMounted) setSecondaryGridData(gData);
      } catch {
        if (isMounted) setSecondaryGridData(null);
      }

      try {
        const statsRes: any = await getStatistics(datasetId, secondaryVariable);
        if (isMounted) {
          if (statsRes?.variables && statsRes.variables[secondaryVariable]) {
            setSecondaryStatistics(statsRes.variables[secondaryVariable]);
          } else if (statsRes?.min !== undefined) {
            setSecondaryStatistics(statsRes);
          }
        }
      } catch {
        if (isMounted) setSecondaryStatistics(null);
      }
    }, 150);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [datasetId, secondaryVariable, timeIndex, depthIndex, regionBounds, analysisMode]);

  // 7. Fetch Currents Analysis & Vector Fields
  useEffect(() => {
    if (!datasetId || (!showVectors && analysisMode !== 'currents')) {
      setVectorData(null);
      setCurrentsAnalysis(null);
      return;
    }

    let isMounted = true;
    const fetchCurrents = async () => {
      setLoading((prev) => ({ ...prev, currents: true }));
      try {
        const [vData, cAnalysis] = await Promise.all([
          getCurrentVectors(datasetId, { time_index: timeIndex, depth_index: depthIndex, stride: 2 }),
          getCurrentsAnalysis(datasetId),
        ]);
        if (isMounted) {
          setVectorData(vData);
          setCurrentsAnalysis(cAnalysis);
        }
      } catch {
        if (isMounted) {
          setVectorData(null);
          setCurrentsAnalysis(null);
        }
      } finally {
        if (isMounted) setLoading((prev) => ({ ...prev, currents: false }));
      }
    };

    fetchCurrents();
    return () => { isMounted = false; };
  }, [datasetId, timeIndex, depthIndex, showVectors, analysisMode]);

  // 8. Fetch Point Probes (Vertical Profile & Time-Series)
  useEffect(() => {
    if (!datasetId || !primaryVariable || probeLat === null || probeLon === null) {
      setProfileData(null);
      setTimeseriesData(null);
      return;
    }

    let isMounted = true;
    const fetchProbes = async () => {
      setLoading((prev) => ({ ...prev, profile: true, timeseries: true }));
      const fetchVar = primaryVariable === 'current_speed' ? 'u' : primaryVariable;

      try {
        const pData = await getProfile(datasetId, fetchVar, probeLat, probeLon, { time_index: timeIndex });
        if (isMounted) setProfileData(pData);
      } catch {
        if (isMounted) setProfileData(null);
      } finally {
        if (isMounted) setLoading((prev) => ({ ...prev, profile: false }));
      }

      try {
        const tData = await getTimeseries(datasetId, fetchVar, probeLat, probeLon, { depth_index: depthIndex });
        if (isMounted) setTimeseriesData(tData);
      } catch {
        if (isMounted) setTimeseriesData(null);
      } finally {
        if (isMounted) setLoading((prev) => ({ ...prev, timeseries: false }));
      }
    };

    fetchProbes();
    return () => { isMounted = false; };
  }, [datasetId, primaryVariable, probeLat, probeLon, timeIndex, depthIndex]);

  // 9. Fetch Transect Cross-Section
  useEffect(() => {
    if (!datasetId || !primaryVariable || analysisMode !== 'transect') {
      setTransectData(null);
      return;
    }

    let isMounted = true;
    const fetchTransect = async () => {
      setLoading((prev) => ({ ...prev, transect: true }));
      const fetchVar = primaryVariable === 'current_speed' ? 'u' : primaryVariable;
      try {
        const tData = await getTransect(datasetId, fetchVar, {
          lat1: transectCoords.lat1,
          lon1: transectCoords.lon1,
          lat2: transectCoords.lat2,
          lon2: transectCoords.lon2,
          num_points: transectCoords.numPoints,
          time_index: timeIndex,
          depth_index: depthIndex,
        });
        if (isMounted) setTransectData(tData);
      } catch {
        if (isMounted) setTransectData(null);
      } finally {
        if (isMounted) setLoading((prev) => ({ ...prev, transect: false }));
      }
    };

    fetchTransect();
    return () => { isMounted = false; };
  }, [datasetId, primaryVariable, transectCoords, timeIndex, depthIndex, analysisMode]);

  // 10. Fetch Dataset Analysis Summary
  useEffect(() => {
    if (!datasetId) {
      setSummaryAnalysis(null);
      return;
    }

    let isMounted = true;
    const fetchSummary = async () => {
      try {
        const sum = await getDatasetSummary(datasetId);
        if (isMounted) setSummaryAnalysis(sum);
      } catch {
        if (isMounted) setSummaryAnalysis(null);
      }
    };

    fetchSummary();
    return () => { isMounted = false; };
  }, [datasetId]);

  // Snapshot Management Operations
  const saveCurrentSnapshot = (name: string, description?: string) => {
    if (!datasetId) return;
    const newSnapshot: ScientificSnapshot = {
      id: `snap_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      name,
      description,
      datasetId,
      datasetName: metadata?.name || 'Scientific Dataset',
      primaryVariable,
      secondaryVariable,
      timeIndex,
      depthIndex,
      probeLat,
      probeLon,
      regionBounds,
      analysisMode,
      colormap,
      speedThreshold,
      displayScale,
      timestamp: new Date().toISOString(),
      appVersion: '1.0.0',
    };
    const updated = saveSnapshot(newSnapshot);
    setSnapshots(updated);
  };

  const loadSnapshot = (snapshot: ScientificSnapshot) => {
    setDatasetId(snapshot.datasetId);
    if (snapshot.primaryVariable) setPrimaryVariable(snapshot.primaryVariable);
    if (snapshot.secondaryVariable) setSecondaryVariable(snapshot.secondaryVariable);
    setTimeIndex(snapshot.timeIndex ?? 0);
    setDepthIndex(snapshot.depthIndex ?? 0);
    setProbeLat(snapshot.probeLat);
    setProbeLon(snapshot.probeLon);
    setRegionBounds(snapshot.regionBounds || null);
    setAnalysisMode(snapshot.analysisMode || 'explore');
    if (snapshot.colormap) setColormap(snapshot.colormap);
    if (snapshot.speedThreshold !== undefined) setSpeedThreshold(snapshot.speedThreshold);
    if (snapshot.displayScale) setDisplayScale(snapshot.displayScale);
  };

  const deleteSnapshotById = (id: string) => {
    const updated = deleteSnapshot(id);
    setSnapshots(updated);
  };

  const renameSnapshotById = (id: string, name: string) => {
    const updated = renameSnapshot(id, name);
    setSnapshots(updated);
  };

  // Annotation Operations
  const addAnnotation = (data: Omit<ScientificAnnotation, 'id' | 'createdAt'>) => {
    const newAnnotation: ScientificAnnotation = {
      ...data,
      id: `ann_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      createdAt: new Date().toISOString(),
    };
    const updated = saveAnnotation(newAnnotation);
    setAnnotations(updated);
  };

  const deleteAnnotationById = (id: string) => {
    const updated = deleteAnnotation(id);
    setAnnotations(updated);
  };

  // Workspace Reset
  const resetWorkspace = () => {
    setTimeIndex(0);
    setDepthIndex(0);
    setRegionBounds(null);
    setDisplayScale({ mode: 'auto' });
    setAnalysisMode('explore');
    if (variables.length > 0) {
      const defaultVar = variables[0];
      setPrimaryVariable(defaultVar.name || defaultVar.variable_name || null);
    }
  };

  const refreshAll = async () => {
    await fetchDatasets();
  };

  return (
    <AnalysisContext.Provider
      value={{
        datasets,
        datasetId,
        setDatasetId,
        metadata,
        variables,
        primaryVariable,
        setPrimaryVariable,
        secondaryVariable,
        setSecondaryVariable,
        timeIndex,
        setTimeIndex,
        depthIndex,
        setDepthIndex,
        probeLat,
        probeLon,
        setProbeCoords,
        regionBounds,
        setRegionBounds,
        clearRegionBounds,
        transectCoords,
        setTransectCoords,
        analysisMode,
        setAnalysisMode,
        colormap,
        setColormap,
        showVectors,
        setShowVectors,
        speedThreshold,
        setSpeedThreshold,
        displayScale,
        setDisplayScale,
        resetDisplayScale,
        isPlaying,
        togglePlay,
        stepForward,
        stepBackward,
        gridData,
        secondaryGridData,
        profileData,
        timeseriesData,
        vectorData,
        transectData,
        statistics,
        secondaryStatistics,
        currentsAnalysis,
        summaryAnalysis,
        snapshots,
        saveCurrentSnapshot,
        loadSnapshot,
        deleteSnapshotById,
        renameSnapshotById,
        annotations,
        addAnnotation,
        deleteAnnotationById,
        isSnapshotModalOpen,
        setIsSnapshotModalOpen,
        isAnnotationDrawerOpen,
        setIsAnnotationDrawerOpen,
        isProvenanceModalOpen,
        setIsProvenanceModalOpen,
        isExportModalOpen,
        setIsExportModalOpen,
        resetWorkspace,
        loading,
        error,
        clearError,
        refreshAll,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = (): AnalysisContextType => {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
};
