/**
 * Dataset API services.
 */

import { apiClient } from "./client";
import type {
  DatasetItem,
  DatasetListResponse,
  FrontendDatasetMetadata,
  VariableDiscoveryResponse,
} from "../types";

export const listDatasets = async (): Promise<DatasetListResponse> => {
  const items = await apiClient<DatasetItem[]>("/api/v1/datasets");
  return { items, total: items.length };
};

export const getDatasetMetadata = async (datasetId: string): Promise<FrontendDatasetMetadata> => {
  return apiClient<FrontendDatasetMetadata>(`/api/v1/datasets/${datasetId}/metadata`);
};

export const getDatasetVariables = async (
  datasetId: string,
  assetId?: string
): Promise<VariableDiscoveryResponse> => {
  const query = assetId ? `?asset_id=${assetId}` : "";
  return apiClient<VariableDiscoveryResponse>(`/api/v1/datasets/${datasetId}/variables${query}`);
};

export const datasetApi = {
  listDatasets,
  getDatasetMetadata,
  getDatasetVariables,
};
