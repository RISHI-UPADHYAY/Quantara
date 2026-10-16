
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import ReviewInvestigationPanel from "./ReviewInvestigationPanel";
import {
  createReviewComment,
  getReviewInvestigation,
  listReviewActivities,
  listReviewComments,
  updateReviewIssues,
  type ReviewActivity,
  type ReviewInvestigation,
  type ReviewIssue,
} from "../../services/reviewQueueService";

vi.mock("../../services/reviewQueueService", () => ({
  createReviewComment: vi.fn(),
  getReviewInvestigation: vi.fn(),
  listReviewActivities: vi.fn(),
  listReviewComments: vi.fn(),
  updateReviewIssues: vi.fn(),
}));

const issueFixture: ReviewIssue = {
  id: "issue-1",
  order_id: "order-1",
  dataset_id: "dataset-1",
  dataset_version_id: "version-1",
  issue_code: "HIGH_SLIPPAGE",
  severity: "HIGH",
  status: "OPEN",
  metric: "slippage_bps",
  observed_value: 12.5,
  threshold: 10,
  message: "Execution slippage exceeded the threshold",
  evidence: { venue: "NSE" },
  recommendations: ["Investigate execution quality"],
  assigned_to: null,
  created_at: "2026-10-15T10:00:00Z",
  updated_at: "2026-10-15T10:00:00Z",
  resolved_at: null,
};

const investigationFixture: ReviewInvestigation = {
  issue: issueFixture,
  order: {
    id: "order-1",
    symbol: "NIFTY",
  },
  fills: [
    {
      id: "fill-1",
      quantity: 10,
      price: 25000,
    },
  ],
  tca: {
    slippage_bps: 12.5,
  },
};

const commentFixture: ReviewActivity = {
  id: "comment-1",
  review_issue_id: "issue-1",
  author_id: "user-1",
  activity_type: "COMMENT",
  comment: "Reviewed the execution data.",
  metadata: {},
  created_at: "2026-10-15T10:05:00Z",
};

const activityFixture: ReviewActivity = {
  id: "activity-1",
  review_issue_id: "issue-1",
  author_id: "user-1",
  activity_type: "STATUS_CHANGED",
  comment: null,
  metadata: { status: "ACKNOWLEDGED" },
  created_at: "2026-10-15T10:06:00Z",
};

const emptyActivityResponse = {
  items: [],
  total: 0,
};

function renderPanel(issue: ReviewIssue = issueFixture) {
  const onUpdated = vi.fn();
  const onClose = vi.fn();

  render(
    <ReviewInvestigationPanel
      organizationId="org-1"
      projectId="project-1"
      issue={issue}
      onUpdated={onUpdated}
      onClose={onClose}
    />,
  );

  return { onUpdated, onClose };
}

describe("ReviewInvestigationPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(getReviewInvestigation).mockResolvedValue(
      investigationFixture,
    );

    vi.mocked(listReviewComments).mockResolvedValue(
      emptyActivityResponse,
    );

    vi.mocked(listReviewActivities).mockResolvedValue(
      emptyActivityResponse,
    );

    vi.mocked(updateReviewIssues).mockImplementation(
      async (_organizationId, _projectId, _issueId, payload) => ({
        ...issueFixture,
        status: payload.status ?? issueFixture.status,
        assigned_to: payload.assigned_to ?? issueFixture.assigned_to,
      }),
    );

    vi.mocked(createReviewComment).mockResolvedValue(commentFixture);
  });

  afterEach(() => {
    cleanup();
  });

  it("loads and displays investigation details", async () => {
    renderPanel();

    expect(
      screen.getByText("Loading investigation from Quantara…"),
    ).toBeTruthy();

    expect(
      await screen.findByText(
        "Execution slippage exceeded the threshold",
      ),
    ).toBeTruthy();

    expect(screen.getByText("HIGH")).toBeTruthy();
    expect(screen.getByText("NIFTY")).toBeTruthy();
    expect(screen.getByText("Investigate execution quality")).toBeTruthy();

    expect(getReviewInvestigation).toHaveBeenCalledWith(
      "org-1",
      "project-1",
      "issue-1",
    );
  });

  it("retries when investigation loading fails", async () => {
    const user = userEvent.setup();

    vi.mocked(getReviewInvestigation)
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(investigationFixture);

    renderPanel();

    expect(await screen.findByRole("alert")).toBeTruthy();

    await user.click(
      screen.getByRole("button", {
        name: "Retry loading investigation",
      }),
    );

    expect(
      await screen.findByText(
        "Execution slippage exceeded the threshold",
      ),
    ).toBeTruthy();

    expect(getReviewInvestigation).toHaveBeenCalledTimes(2);
  });

  it("updates the status and notifies the dashboard", async () => {
    const user = userEvent.setup();
    const updatedIssue: ReviewIssue = {
      ...issueFixture,
      status: "ACKNOWLEDGED",
    };

    vi.mocked(updateReviewIssues).mockResolvedValueOnce(updatedIssue);

    const { onUpdated } = renderPanel();

    await screen.findByText(
      "Execution slippage exceeded the threshold",
    );

    await user.click(
      screen.getByRole("button", { name: "ACKNOWLEDGED" }),
    );

    await waitFor(() => {
      expect(updateReviewIssues).toHaveBeenCalledWith(
        "org-1",
        "project-1",
        "issue-1",
        { status: "ACKNOWLEDGED" },
      );
    });

    await waitFor(() => {
      expect(onUpdated).toHaveBeenCalledWith(updatedIssue);
    });

    expect(
      screen.getByText("Current status: ACKNOWLEDGED"),
    ).toBeTruthy();
  });

  it("does not offer further status transitions for a terminal issue", async () => {
    const resolvedIssue: ReviewIssue = {
      ...issueFixture,
      status: "RESOLVED",
      resolved_at: "2026-10-15T11:00:00Z",
    };

    const resolvedInvestigation: ReviewInvestigation = {
      ...investigationFixture,
      issue: resolvedIssue,
    };

    vi.mocked(getReviewInvestigation).mockResolvedValueOnce(
      resolvedInvestigation,
    );

    renderPanel(resolvedIssue);

    expect(
      await screen.findByText("Current status: RESOLVED"),
    ).toBeTruthy();

    expect(
      screen.getByText(
        "This review is in a terminal status and cannot be transitioned further.",
      ),
    ).toBeTruthy();

    expect(
      screen.queryByRole("button", { name: "ACKNOWLEDGED" }),
    ).toBeNull();

    expect(updateReviewIssues).not.toHaveBeenCalled();
  });

  it("submits a comment and refreshes the timeline", async () => {
    const user = userEvent.setup();

    vi.mocked(listReviewComments)
      .mockResolvedValueOnce(emptyActivityResponse)
      .mockResolvedValueOnce({
        items: [commentFixture],
        total: 1,
      });

    const { } = renderPanel();

    await screen.findByText(
      "Execution slippage exceeded the threshold",
    );

    await user.type(
      screen.getByRole("textbox", {
        name: "Add an investigation comment",
      }),
      "  Please investigate this execution.  ",
    );

    await user.click(
      screen.getByRole("button", { name: "Add comment" }),
    );

    await waitFor(() => {
      expect(createReviewComment).toHaveBeenCalledWith(
        "org-1",
        "project-1",
        "issue-1",
        { comment: "Please investigate this execution." },
      );
    });

    expect(
      await screen.findByText("Reviewed the execution data."),
    ).toBeTruthy();

    expect(listReviewComments).toHaveBeenCalledTimes(2);
  });

  it("renders activity history returned by the API", async () => {
    vi.mocked(listReviewActivities).mockResolvedValueOnce({
      items: [activityFixture],
      total: 1,
    });

    renderPanel();

    expect(
      await screen.findByText("Execution slippage exceeded the threshold"),
    ).toBeTruthy();

    expect(await screen.findByText("Status Changed")).toBeTruthy();
  });
});
