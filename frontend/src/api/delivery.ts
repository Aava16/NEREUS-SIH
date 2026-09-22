/**
 * Scientific data delivery API services.
 */

import { apiClient } from "./client";
import type {
  CurrentsDeliveryResponse,
  GridDeliveryResponse,
  ProfileDeliveryResponse,
  TimeSeriesDeliveryResponse,
  TransectDeliveryResponse,
} from "../types";

export interface GridQueryParams {
  time_index?: number;
  depth_index?: number;
  min_lat?: number;
  max_lat?: number;
  min_lon?: number;
  max_lon?: number;
  decimation?: number;
  asset_id?: string;
}

export interface ProfileQueryParams {
  latitude?: number;
  longitude?: number;
  lat?: number;
  lon?: number;
  time_index?: number;
  asset_id?: string;
}

export interface TimeSeriesQueryParams {
  latitude?: number;
  longitude?: number;
  lat?: number;
  lon?: number;
  depth?: number;
  depth_index?: number;
  start_time?: string;
  end_time?: string;
  decimation?: number;
  asset_id?: string;
}

export interface CurrentsQueryParams {
  u_var?: string;
  v_var?: string;
  w_var?: string;
  time_index?: number;
  depth_index?: number;
  min_lat?: number;
  max_lat?: number;
  min_lon?: number;
  max_lon?: number;
  stride?: number;
  decimation?: number;
  asset_id?: string;
}

export interface TransectQueryParams {
  lat1: number;
  lon1: number;
  lat2: number;
  lon2: number;
  num_points?: number;
  time_index?: number;
  depth_index?: number;
  asset_id?: string;
}

function buildQueryString(params: Record<string, any>): string {
  const query = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== null) {
      query.append(key, String(val));
    }
  }
  const str = query.toString();
  return str ? `?${str}` : "";
}

export const getGrid = async (
  datasetId: string,
  variable: string,
  params: GridQueryParams = {}
): Promise<GridDeliveryResponse> => {
  const qs = buildQueryString(params);
  return apiClient<GridDeliveryResponse>(
    `/api/v1/datasets/${datasetId}/variables/${encodeURIComponent(variable)}/grid${qs}`
  );
};

export const getProfile = async (
  datasetId: string,
  variable: string,
  latOrParams: number | ProfileQueryParams,
  lon?: number,
  extraParams?: Partial<ProfileQueryParams>
): Promise<ProfileDeliveryResponse> => {
  let params: Record<string, any> = {};
  if (typeof latOrParams === 'number') {
    params.latitude = latOrParams;
    params.longitude = lon;
    if (extraParams) Object.assign(params, extraParams);
  } else {
    params = { ...latOrParams };
  }
  const qs = buildQueryString(params);
  return apiClient<ProfileDeliveryResponse>(
    `/api/v1/datasets/${datasetId}/variables/${encodeURIComponent(variable)}/profile${qs}`
  );
};

export const getTimeseries = async (
  datasetId: string,
  variable: string,
  latOrParams: number | TimeSeriesQueryParams,
  lon?: number,
  extraParams?: Partial<TimeSeriesQueryParams>
): Promise<TimeSeriesDeliveryResponse> => {
  let params: Record<string, any> = {};
  if (typeof latOrParams === 'number') {
    params.latitude = latOrParams;
    params.longitude = lon;
    if (extraParams) Object.assign(params, extraParams);
  } else {
    params = { ...latOrParams };
  }
  const qs = buildQueryString(params);
  return apiClient<TimeSeriesDeliveryResponse>(
    `/api/v1/datasets/${datasetId}/variables/${encodeURIComponent(variable)}/timeseries${qs}`
  );
};

export const getCurrentVectors = async (
  datasetId: string,
  params: CurrentsQueryParams = {}
): Promise<CurrentsDeliveryResponse> => {
  const qs = buildQueryString(params);
  return apiClient<CurrentsDeliveryResponse>(
    `/api/v1/datasets/${datasetId}/currents/vectors${qs}`
  );
};

export const getTransect = async (
  datasetId: string,
  variable: string,
  params: TransectQueryParams
): Promise<TransectDeliveryResponse> => {
  const qs = buildQueryString(params);
  return apiClient<TransectDeliveryResponse>(
    `/api/v1/datasets/${datasetId}/variables/${encodeURIComponent(variable)}/transect${qs}`
  );
};

export const deliveryApi = {
  getGrid,
  getProfile,
  getTimeseries,
  getCurrentVectors,
  getTransect,
};
