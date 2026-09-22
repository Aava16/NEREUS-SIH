/**
 * System and database health API services.
 */

import { apiClient } from "./client";
import type { SystemHealth } from "../types";

export const checkHealth = async (): Promise<{ status: string }> => {
  return apiClient<{ status: string }>("/api/v1/health");
};

export const checkDbHealth = async (): Promise<SystemHealth> => {
  return apiClient<SystemHealth>("/api/v1/health/db");
};

export const healthApi = {
  checkHealth,
  checkDbHealth,
};
