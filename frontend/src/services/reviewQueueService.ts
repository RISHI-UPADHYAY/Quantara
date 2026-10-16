import api from "./api";

//Types matching the existing backend schemas

export type ReviewSeverity = "MEDIUM" | "HIGH" | "CRITICAL"

export type ReviewStatus = 
    | "OPEN"
    | "ACKNOWLEDGED"
    | "IN_REVIEW"
    | "RESOLVED"
    | "IGNORED"


export interface ReviewIssue {
    id: string
    order_id: string
    dataset_id: string
    dataset_version_id: string
    issue_code: string
    severity: ReviewSeverity
    status: ReviewStatus
    metric: string
    observed_value: number
    threshold: number | null
    message: string
    evidence: Record<string, unknown>
    recommendations: unknown[]
    assigned_to: string | null
    created_at: string
    updated_at: string
    resolved_at: string | null
}

export interface ReviewQueueResponse {
    items: ReviewIssue[]
    total: number
    limit: number
    offset: number
}

export interface ReviewActivity {
    id: string
    review_issue_id: string
    author_id: string | null
    activity_type: string
    comment: string | null
    metadata: Record<string, unknown>
    created_at: string
}

export interface ReviewActivityListResponse {
    items: ReviewActivity[]
    total: number
}

export interface ReviewInvestigation {
    issue: ReviewIssue
    order: {
        id: string
        [key: string]: unknown
    }
    fills: Array<Record<string, unknown>>
    tca: Record<string, unknown>
}

export interface ListReviewIssuesParams {
    status?: ReviewStatus
    severity?: ReviewSeverity
    issue_code?: string
    order_id?: string
    assigned_to?: string
    limit?: number
    offset?: number
}

export interface UpdateReviewIssuePayload {
    status?: ReviewStatus
    assigned_to?: string
}

export interface CreateReviewCommentPayload {
    comment: string
}

//Shared URL builder

function reviewBasePath (
    organizationId: string,
    projectId: string,
): string {
    return (
        `/organizations/${encodeURIComponent(organizationId)}` +
        `/projects/${encodeURIComponent(projectId)}/execution/review`
    )
}


function issuePath (
    organizationId: string,
    projectId: string,
    issueId: string,
): string {
    return (
        `${reviewBasePath(organizationId, projectId)}` + 
        `/${encodeURIComponent(issueId)}`
    )
}


//Review Queue
export async function listReviewIssues (
    organizationId: string,
    projectId: string,
    params: ListReviewIssuesParams = {},
): Promise<ReviewQueueResponse> {
    const response = await api.get<ReviewQueueResponse>(
        reviewBasePath(organizationId, projectId),
        { params },
    )

    return response.data
}


export async function getReviewIssue (
    organizationId: string,
    projectId: string,
    issueId: string,
): Promise<ReviewIssue> {
    const response = await api.get<ReviewIssue>(
        issuePath(organizationId, projectId, issueId),
    )

    return response.data
}


export async function updateReviewIssues (
    organizationId: string,
    projectId: string,
    issueId: string,
    payload: UpdateReviewIssuePayload,
): Promise<ReviewIssue> {
    if (payload.status === undefined && payload.assigned_to === undefined) {
        throw new Error (
            "Provide a review status or an assignee to update the issue.",
        )
    }

    const response = await api.patch<ReviewIssue>(
        issuePath(organizationId, projectId, issueId),
        payload,
    )

    return response.data
}


//Investigation details
export async function getReviewInvestigation (
    organizationId: string,
    projectId: string,
    issueId: string,
): Promise<ReviewInvestigation> {
    const response = await api.get<ReviewInvestigation>(
        `${issuePath(organizationId, projectId, issueId)}/investigation`,
    )

    return response.data
}


//Comments
export async function listReviewComments (
    organizationId: string,
    projectId: string,
    issueId: string,
    params: { limit?: number; offset?: number } = {},
): Promise<ReviewActivityListResponse> {
    const response = await api.get<ReviewActivityListResponse>(
        `${issuePath(organizationId, projectId, issueId)}/comments`,
        { params },
    )

    return response.data
}


export async function createReviewComment (
    organizationId: string,
    projectId: string,
    issueId: string,
    payload: CreateReviewCommentPayload,
): Promise<ReviewActivity> {
    const comment = payload.comment.trim()

    if (!comment) {
        throw new Error(
            "A comment cannot be empty."
        )
    }

    if (comment.length > 5000) {
        throw new Error(
            "A comment cannot exceed 5,000 characters."
        )
    }

    const response = await api.post<ReviewActivity>(
        `${issuePath(organizationId, projectId, issueId)}/comments`,
        { comment },
    )

    return response.data
}


//Activity history
export async function listReviewActivities (
    organizationId: string,
    projectId: string,
    issueId: string,
    params: { limit?: number; offset?: number } = {},
): Promise<ReviewActivityListResponse> {
    const response = await api.get<ReviewActivityListResponse>(
        `${issuePath(organizationId, projectId, issueId)}/activities`,
        { params },
    )

    return response.data
}