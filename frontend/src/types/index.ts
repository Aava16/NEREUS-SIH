/**
 * TypeScript type definitions for NEREUS Scientific Visualization & Analytics Platform.
 */

export interface SpatialExtent {
  latitude_min?: number;
  latitude_max?: number;
  longitude_min?: number;
  longitude_max?: number;
  latitude_points?: number;
  longitude_points?: number;
  latitude_step?: number | null;
  longitude_step?: number | null;
  min_lat?: number;
  max_lat?: number;
  min_lon?: number;
  max_lon?: number;
}

export interface DepthRange {
  depth_min?: number | null;
  depth_max?: number | null;
  depth_levels_count?: number;
  levels?: number[];
  length?: number;
}

export interface TemporalRange {
  start_time?: string;
  end_time?: string;
  start?: string;
  end?: string;
  total_timesteps?: number;
  time_steps_count?: number;
  timestep_interval_seconds?: number | null;
  is_regular_interval?: boolean;
}

export interface DatasetItem {
  id: string;
  name: string;
  title?: string;
  description?: string | null;
  source?: string | null;
  source_uri?: string | null;
  dataset_type?: string;
  temporal_start?: string | null;
  temporal_end?: string | null;
  status?: string;
  created_at?: string;
  updated_at?: string;
  spatial_coverage?: SpatialExtent;
  temporal_coverage?: TemporalRange;
  variable_names?: string[];
}

export type DatasetListItem = DatasetItem;

export interface DatasetListResponse {
  items: DatasetItem[];
  total?: number;
}

export interface FrontendDatasetMetadata {
  id?: string;
  dataset_id?: string;
  name: string;
  title?: string;
  description?: string | null;
  source?: string | null;
  source_uri?: string | null;
  dataset_type?: string;
  variables?: string[];
  dimensions?: Record<string, number>;
  spatial_extent?: SpatialExtent;
  spatial_coverage?: SpatialExtent;
  depth_extent?: DepthRange;
  depth_levels?: number[];
  temporal_extent?: TemporalRange | null;
  temporal_coverage?: TemporalRange | null;
  status?: string;
  primary_asset_id?: string | null;
  primary_asset_format?: string | null;
  metadata_json?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export type DatasetDetailResponse = FrontendDatasetMetadata;

export interface VariableMetadataItem {
  name: string;
  variable_name?: string;
  standard_name?: string | null;
  long_name?: string | null;
  units?: string | null;
  dtype?: string;
  data_type?: string;
  dimensions?: string[];
  shape?: number[];
  valid_min?: number | null;
  valid_max?: number | null;
  fill_value?: number | null;
  is_derived?: boolean;
  attributes?: Record<string, any>;
}

export type DatasetVariableInfo = VariableMetadataItem;

export interface VariableDiscoveryResponse {
  dataset_id: string;
  dataset_name?: string;
  asset_id?: string | null;
  variables: VariableMetadataItem[];
  total_variables?: number;
}

export interface DownsampleMetadata {
  downsampled: boolean;
  original_points?: number;
  returned_points?: number;
  decimation_factor?: number;
}

export interface GridDeliveryResponse {
  dataset_id: string;
  variable?: string;
  variable_name?: string;
  units?: string | null;
  time?: string | null;
  depth?: number | null;
  latitudes: number[];
  longitudes: number[];
  values: (number | null)[][];
  min_value?: number;
  max_value?: number;
  downsample?: DownsampleMetadata;
  delivered_at?: string;
}

export type GridDataResponse = GridDeliveryResponse;

export interface ProfileDeliveryResponse {
  dataset_id: string;
  variable?: string;
  variable_name?: string;
  units?: string | null;
  requested_latitude?: number;
  requested_longitude?: number;
  actual_latitude?: number;
  actual_longitude?: number;
  lat: number;
  lon: number;
  time?: string | null;
  timestamp?: string;
  depth_units?: string;
  depths: number[];
  values: (number | null)[];
  valid_levels?: number;
  min_value?: number;
  max_value?: number;
  delivered_at?: string;
}

export type DepthProfileResponse = ProfileDeliveryResponse;

export interface TimeSeriesPoint {
  timestamp: string;
  value?: number | null;
}

export interface TimeSeriesDeliveryResponse {
  dataset_id: string;
  variable?: string;
  variable_name?: string;
  units?: string | null;
  latitude?: number;
  longitude?: number;
  lat: number;
  lon: number;
  depth?: number | null;
  timestamps: string[];
  values: (number | null)[];
  points?: TimeSeriesPoint[];
  total_points?: number;
  min_value?: number;
  max_value?: number;
  downsample?: DownsampleMetadata;
  delivered_at?: string;
}

export type PointTimeseriesResponse = TimeSeriesDeliveryResponse;

export interface CurrentVectorItem {
  lat: number;
  lon: number;
  latitude?: number;
  longitude?: number;
  u: number;
  v: number;
  w?: number | null;
  speed: number;
  direction?: number | null;
}

export interface CurrentsDeliveryResponse {
  dataset_id: string;
  dataset_name?: string;
  velocity_dimensions?: string;
  time?: string | null;
  depth?: number | null;
  vectors: CurrentVectorItem[];
  total_vectors?: number;
  speed_min?: number | null;
  speed_max?: number | null;
  min_speed?: number;
  max_speed?: number;
  downsample?: DownsampleMetadata;
  delivered_at?: string;
}

export type VelocityVectorsResponse = CurrentsDeliveryResponse;

export interface TransectPoint {
  latitude: number;
  longitude: number;
  distance_km: number;
  value?: number | null;
}

export interface TransectDeliveryResponse {
  dataset_id: string;
  variable_name: string;
  units?: string | null;
  time?: string | null;
  depth?: number | null;
  start_latitude: number;
  start_longitude: number;
  end_latitude: number;
  end_longitude: number;
  points: TransectPoint[];
  total_points: number;
  total_distance_km: number;
  min_value?: number | null;
  max_value?: number | null;
  delivered_at: string;
}

export interface VariableStatistics {
  name?: string;
  variable_name?: string;
  units?: string | null;
  standard_name?: string | null;
  min?: number | null;
  max?: number | null;
  mean?: number | null;
  median?: number | null;
  std?: number | null;
  p25?: number | null;
  p50?: number | null;
  p75?: number | null;
  p90?: number | null;
  p95?: number | null;
  valid_count?: number;
  missing_count?: number;
  fill_value?: number | null;
  shape?: number[];
}

export type VariableStatisticsResponse = VariableStatistics;

export interface DatasetStatisticsResponse {
  dataset_id: string;
  dataset_name?: string;
  asset_id?: string | null;
  variables: Record<string, VariableStatistics>;
  analyzed_at?: string;
}

export interface SpatialAnalysisResponse {
  dataset_id: string;
  dataset_name: string;
  spatial_extent: SpatialExtent;
  depth_extent: DepthRange;
}

export interface TemporalAnalysisResponse {
  dataset_id: string;
  dataset_name: string;
  temporal_extent: TemporalRange;
}

export interface CurrentsAnalysisResponse {
  dataset_id: string;
  dataset_name: string;
  speed: VariableStatistics;
  direction?: VariableStatistics;
  u: VariableStatistics;
  v: VariableStatistics;
  w?: VariableStatistics;
}

export interface DatasetAnalysisSummaryResponse {
  dataset_id: string;
  dataset_name: string;
  spatial: SpatialAnalysisResponse;
  temporal: TemporalAnalysisResponse;
  key_variables: Record<string, VariableStatistics>;
}

export interface SystemHealth {
  status: string;
  database?: string;
  version?: string;
  timestamp?: string;
}

export type AnalysisMode = 
  | "explore"
  | "compare"
  | "timeseries"
  | "profile"
  | "currents"
  | "transect"
  | "anomaly";

export type VisualizationMode = "grid" | "vectors" | "profile" | "timeseries" | "scatter" | "transect";
export type ColormapName = "viridis" | "plasma" | "thermal" | "haline" | "coolwarm" | "turbo";

export interface TransectCoords {
  lat1: number;
  lon1: number;
  lat2: number;
  lon2: number;
  numPoints: number;
}

export interface RegionBounds {
  minLat: number;
  maxLat: number;
  minLon: number;
  maxLon: number;
}

export type DisplayScaleMode = "auto" | "percentile" | "manual";

export interface DisplayScaleConfig {
  mode: DisplayScaleMode;
  manualMin?: number;
  manualMax?: number;
}

export interface ScientificSnapshot {
  id: string;
  name: string;
  description?: string;
  datasetId: string;
  datasetName?: string;
  primaryVariable: string | null;
  secondaryVariable: string | null;
  timeIndex: number;
  depthIndex: number;
  probeLat: number | null;
  probeLon: number | null;
  regionBounds: RegionBounds | null;
  analysisMode: AnalysisMode;
  colormap: ColormapName;
  speedThreshold: number;
  displayScale: DisplayScaleConfig;
  timestamp: string;
  appVersion: string;
}

export interface ScientificAnnotation {
  id: string;
  title: string;
  note: string;
  latitude: number;
  longitude: number;
  timeIndex?: number;
  timestampStr?: string;
  depthIndex?: number;
  depthStr?: string;
  variable: string;
  observedValue?: number | null;
  units?: string | null;
  datasetId: string;
  datasetName?: string;
  createdAt: string;
  updatedAt?: string;
}

export type ExportFormat = "csv" | "json" | "png" | "report";

