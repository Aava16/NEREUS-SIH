/**
 * Scientific analysis API services.
 */

import { apiClient } from "./client";
import type { 
  DatasetStatisticsResponse, 
  VariableStatisticsResponse,
  SpatialAnalysisResponse,
  TemporalAnalysisResponse,
  CurrentsAnalysisResponse,
  DatasetAnalysisSummaryResponse
} from "../types";

export const getStatistics = async (
  datasetId: string,
  variable?: string,
  assetId?: string
): Promise<VariableStatisticsResponse | DatasetStatisticsResponse> => {
  const params = new URLSearchParams();
  if (variable) params.append("variable", variable);
  if (assetId) params.append("asset_id", assetId);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiClient<VariableStatisticsResponse | DatasetStatisticsResponse>(
    `/api/v1/analysis/datasets/${datasetId}/statistics${qs}`
  );
};

export const getSpatialAnalysis = async (
  datasetId: string,
  assetId?: string
): Promise<SpatialAnalysisResponse> => {
  const qs = assetId ? `?asset_id=${assetId}` : "";
  return apiClient<SpatialAnalysisResponse>(`/api/v1/analysis/datasets/${datasetId}/spatial${qs}`);
};

export const getTemporalAnalysis = async (
  datasetId: string,
  assetId?: string
): Promise<TemporalAnalysisResponse> => {
  const qs = assetId ? `?asset_id=${assetId}` : "";
  return apiClient<TemporalAnalysisResponse>(`/api/v1/analysis/datasets/${datasetId}/temporal${qs}`);
};

export const getCurrentsAnalysis = async (
  datasetId: string,
  u_var?: string,
  v_var?: string,
  w_var?: string,
  assetId?: string
): Promise<CurrentsAnalysisResponse> => {
  const params = new URLSearchParams();
  if (u_var) params.append("u_var", u_var);
  if (v_var) params.append("v_var", v_var);
  if (w_var) params.append("w_var", w_var);
  if (assetId) params.append("asset_id", assetId);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiClient<CurrentsAnalysisResponse>(`/api/v1/analysis/datasets/${datasetId}/currents${qs}`);
};

export const getDatasetSummary = async (
  datasetId: string,
  assetId?: string
): Promise<DatasetAnalysisSummaryResponse> => {
  const qs = assetId ? `?asset_id=${assetId}` : "";
  return apiClient<DatasetAnalysisSummaryResponse>(`/api/v1/analysis/datasets/${datasetId}/summary${qs}`);
};

export const analysisApi = {
  getStatistics,
  getSpatialAnalysis,
  getTemporalAnalysis,
  getCurrentsAnalysis,
  getDatasetSummary,
};
