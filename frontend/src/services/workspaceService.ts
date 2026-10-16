import api from "./api";

/**
 * Organization returned by GET /api/v1/organizations.
 */
export interface Organization {
  id: string;
  name: string;
  slug: string;
}

/**
 * Project returned by GET /api/v1/organizations/{organization_id}/projects.
 */
export interface Project {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description: string | null;
  created_by: string;
}

export interface PilotWorkspacePeriod {
  start: string | null;
  end: string | null;   
}

export interface PilotWorkspaceExecution {
  orders: number;
  filled_orders: number;
  partially_filled_orders: number;
  unfilled_orders: number;
  fill_rate: number;
  ordered_quantity: number;
  executed_quantity: number;
  total_notional: number;
  average_slippage_percentage: number | null;
  weighted_slippage_percentage: number | null;
  average_shortfall_percentage: number | null;
  weighted_shortfall_percentage: number | null;
  average_vwap_deviation_percentage: number | null;
  weighted_vwap_deviation_percentage: number | null;
  analyzed_orders: number;
  failed_orders: number;
  tca_requested_orders: number;
  tca_coverage_percentage: number;
}

export interface PilotWorkspaceQuality {
  analyzed_orders: number;
  coverage_percentage: number;
  excellent: number;
  good: number;
  fair: number;
  poor: number;
  unknown: number;
}

export interface PilotWorkspaceExceptions {
  total: number;
  open: number;
  acknowledged: number;
  in_review: number;
  resolved: number;
  ignored: number;
  medium: number;
  high: number;
  critical: number;
}

export interface PilotWorkspaceBreakdownItem {
  name: string;
  orders: number;
  analyzed_orders: number;
  total_notional: number;
  fill_rate: number;
  weighted_slippage_percentage: number | null;
  weighted_shortfall_percentage: number | null;
  weighted_vwap_deviation_percentage: number | null;
}

export interface PilotWorkspaceReview {
  id: string;
  order_id: string;
  issue_code: string;
  severity: string;
  status: string;
  metric: string | null;
  observed_value: number | null;
  threshold_value: number | null;
  message: string | null;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface PilotWorkspaceMarketData {
  dataset_id: string | null;
  dataset_version_id: string | null;
  version: number | null;
}

export interface PilotWorkspaceOverview {
  organization_id: string;
  project_id: string;
  period: PilotWorkspacePeriod;
  execution: PilotWorkspaceExecution;
  quality: PilotWorkspaceQuality;
  exceptions: PilotWorkspaceExceptions;
  top_symbols: PilotWorkspaceBreakdownItem[];
  top_venues: PilotWorkspaceBreakdownItem[];
  recent_reviews: PilotWorkspaceReview[];
  market_data: PilotWorkspaceMarketData;
}

/**
 * Lists organizations accessible to the authenticated user.
 */
export async function getOrganizations(): Promise<Organization[]> {
  const response = await api.get<Organization[]>("/organizations");
  return response.data;
}

/**
 * Lists projects belonging to an organization.
 */
export async function getProjects(
  organizationId: string,
): Promise<Project[]> {
  const response = await api.get<Project[]>(
    `/organizations/${encodeURIComponent(organizationId)}/projects`,
  );

  return response.data;
}

/**
 * Fetches the pilot overview for an organization and project.
 *
 * Optional date boundaries must be ISO-8601 timestamps.
 */
export async function getPilotWorkspaceOverview(
  organizationId: string,
  projectId: string,
  period?: {
    startTime?: string;
    endTime?: string;
  },
): Promise<PilotWorkspaceOverview> {
  const params: Record<string, string> = {};

  if (period?.startTime) {
    params.start_time = period.startTime;
  }

  if (period?.endTime) {
    params.end_time = period.endTime;
  }

  const response = await api.get<PilotWorkspaceOverview>(
    `/organizations/${encodeURIComponent(organizationId)}/projects/${encodeURIComponent(projectId)}/pilot/overview`,
    { params },
  );

  return response.data;
}