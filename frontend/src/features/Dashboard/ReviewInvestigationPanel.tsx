import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  LoaderCircle,
  X,
} from "lucide-react";
import {
  createReviewComment,
  getReviewInvestigation,
  listReviewActivities,
  listReviewComments,
  updateReviewIssues,
  type ReviewActivity,
  type ReviewInvestigation,
  type ReviewIssue,
  type ReviewStatus
} from "../../services/reviewQueueService";
import { getApiErrorMessage } from "../../services/api";

interface ReviewInvestigationPanelProps {
  organizationId: string;
  projectId: string;
  issue: ReviewIssue;
  onUpdated: (issue: ReviewIssue) => void;
  onClose: () => void;
}

function formatLabel(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "number") {
    return Number.isFinite(value) ? value.toLocaleString() : "—";
  }

  if (typeof value === "string") {
    return value;
  }

  return "";
}

function DetailGrid({
  data,
}: {
  data: Record<string, unknown>;
}) {
  const entries = Object.entries(data).filter(
    ([, value]) =>
      value === null ||
      value === undefined ||
      typeof value !== "object",
  );

  if (entries.length === 0) {
    return <p style={styles.muted}>No scalar details available.</p>;
  }

  return (
    <div style={styles.detailGrid}>
      {entries.map(([key, value]) => (
        <div key={key} style={styles.detailItem}>
          <span style={styles.detailLabel}>{formatLabel(key)}</span>
          <span style={styles.detailValue}>
            {formatValue(value) || "Structured data"}
          </span>
        </div>
      ))}
    </div>
  );
}

function StructuredDetails({
  title,
  value,
}: {
  title: string;
  value: unknown;
}) {
  if (value === null || value === undefined) {
    return (
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>{title}</h3>
        <p style={styles.muted}>Not available for this review.</p>
      </section>
    );
  }

  if (Array.isArray(value)) {
    return (
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>{title}</h3>
        {value.length === 0 ? (
          <p style={styles.muted}>No records available.</p>
        ) : (
          <div style={styles.stack}>
            {value.map((item, index) => (
              <div key={index} style={styles.record}>
                {item && typeof item === "object" ? (
                  <DetailGrid data={item as Record<string, unknown>} />
                ) : (
                  <span>{formatValue(item)}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    );
  }

  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);

    return (
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>{title}</h3>
        {entries.length === 0 ? (
          <p style={styles.muted}>No details available.</p>
        ) : (
          <div style={styles.stack}>
            {entries.map(([key, nestedValue]) => (
              <div key={key} style={styles.record}>
                {nestedValue !== null &&
                typeof nestedValue === "object" ? (
                  <StructuredDetails
                    title={formatLabel(key)}
                    value={nestedValue}
                  />
                ) : (
                  <div style={styles.detailItem}>
                    <span style={styles.detailLabel}>
                      {formatLabel(key)}
                    </span>
                    <span style={styles.detailValue}>
                      {formatValue(nestedValue) || "—"}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    );
  }

  return (
    <section style={styles.section}>
      <h3 style={styles.sectionTitle}>{title}</h3>
      <p>{formatValue(value)}</p>
    </section>
  );
}

const NEXT_REVIEW_STATUSES: Record<ReviewStatus, ReviewStatus[]> = {
    OPEN: ["ACKNOWLEDGED", "IN_REVIEW", "IGNORED"],
    ACKNOWLEDGED: ["IN_REVIEW", "RESOLVED", "IGNORED"],
    IN_REVIEW: ["RESOLVED", "IGNORED"],
    RESOLVED: [],
    IGNORED: [],
};

function getStatusLabel(status: ReviewStatus): string {
    return status.replaceAll("_", " ");
}

export default function ReviewInvestigationPanel({
  organizationId,
  projectId,
  issue,
  onUpdated,
  onClose,
}: ReviewInvestigationPanelProps) {
  const [investigation, setInvestigation] =
    useState<ReviewInvestigation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retryCount, setRetryCount] = useState(0);
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [actionError, setActionError] = useState("");
  const [commentText, setCommentText] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [comments, setComments] = useState<ReviewActivity[]>([]);
  const [activities, setActivities] = useState<ReviewActivity[]>([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState("");
  const [timelineReload, setTimelineReload] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadTimeline() {
        setTimelineLoading(true);
        setTimelineError("");

        try {
            const [commentResult, activityResult] = await Promise.all([
                listReviewComments(organizationId, projectId, issue.id, {
                    limit: 100,
                    offset: 0,
                }),
                listReviewActivities(organizationId, projectId, issue.id, {
                    limit: 100,
                    offset: 0,
                }),
            ]);

            if (!cancelled) {
                setComments(commentResult.items);
                setActivities(activityResult.items);
            } 
        } catch (error) {
            if (!cancelled) {
                setTimelineError(
                    getApiErrorMessage(error, "Unable to load review activity."),
                );
            }
        } finally {
            if (!cancelled) {
                setTimelineLoading(false);
            }
        }
    }

    void loadTimeline();

    return () => {
        cancelled = true;
    };
  }, [organizationId, projectId, issue.id, timelineReload]);

  useEffect(() => {
    let cancelled = false;

    async function loadInvestigation() {
      setLoading(true);
      setError("");
      setInvestigation(null);

      try {
        const result = await getReviewInvestigation(
          organizationId,
          projectId,
          issue.id,
        );

        if (!cancelled) {
          setInvestigation(result);
        }
      } catch {
        if (!cancelled) {
          setError(
            "Unable to load investigation details. Check your access and connection, then retry.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadInvestigation();

    return () => {
      cancelled = true;
    };
  }, [organizationId, projectId, issue.id, retryCount]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const activeIssue = investigation?.issue ?? issue;
  const order = investigation?.order;

  async function handleStatusChange(nextStatus: ReviewStatus) {
    const allowedStatuses = NEXT_REVIEW_STATUSES[activeIssue.status];

    if (!allowedStatuses.includes(nextStatus) || statusUpdating) {
        return;
    }
    
    setStatusUpdating(true);
    setActionError("");

    try {
        const updatedIssue = await updateReviewIssues(
            organizationId, 
            projectId,
            issue.id,
            { status: nextStatus },
        );

        setInvestigation((current) => 
            current ? { ...current, issue: updatedIssue } : current,
        );

        onUpdated(updatedIssue);
        setTimelineReload((value) => value + 1);
    } catch (error) {
        setActionError(
                getApiErrorMessage(error, "Unable to update review status."),
        );
    } finally {
        setStatusUpdating(false);
    }
  }

  async function handleCommentSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const comment = commentText.trim();

    if (!comment || comment.length > 5000 || commentSubmitting) {
        return;
    }

    setCommentSubmitting(true);
    setActionError("");

    try {
        await createReviewComment(
            organizationId,
            projectId,
            issue.id,
            { comment },
        );

        setCommentText("");
        setTimelineReload((value) => value + 1);
    } catch (error) {
        setActionError(
            getApiErrorMessage(error, "Unable to submit review comment."),
        );
    } finally {
        setCommentSubmitting(false);
    }
  }

  return (
    <div
      role="presentation"
      style={styles.backdrop}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="review-investigation-title"
        style={styles.dialog}
      >
        <header style={styles.header}>
          <div>
            <p style={styles.eyebrow}>EXECUTION REVIEW</p>
            <h2 id="review-investigation-title" style={styles.title}>
              {activeIssue.message || formatLabel(activeIssue.issue_code)}
            </h2>
            <p style={styles.muted}>
              Issue {activeIssue.id} · Order {activeIssue.order_id}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close investigation"
            style={styles.closeButton}
          >
            <X size={20} aria-hidden="true" />
          </button>
        </header>

        <div style={styles.body}>
          {loading && (
            <div role="status" style={styles.feedback}>
              <LoaderCircle size={18} aria-hidden="true" />
              Loading investigation from Quantara…
            </div>
          )}

          {error && !loading && (
            <div role="alert" style={styles.error}>
              <AlertCircle size={20} aria-hidden="true" />
              <div>
                <p>{error}</p>
                <button
                  type="button"
                  style={styles.secondaryButton}
                  onClick={() => {
                    setRetryCount((count) => count + 1)
                  }}
                >
                  Retry loading investigation
                </button>
              </div>
            </div>
          )}

          {!loading && !error && investigation && (
            <>
              <section style={styles.section}>
                <h3 style={styles.sectionTitle}>Review actions</h3>

                <p style={styles.muted}>
                    Current status: {getStatusLabel(activeIssue.status)}
                </p>

                <div style={styles.actionRow}>
                    {NEXT_REVIEW_STATUSES[activeIssue.status].map((status) => (
                        <button
                            key={status}
                            type="button"
                            style={styles.secondaryButton}
                            disabled={statusUpdating}
                            onClick={() => void handleStatusChange(status)}
                        >
                            {statusUpdating ? "Updating..." : getStatusLabel(status)}
                        </button>
                    ))}
                </div>

                {NEXT_REVIEW_STATUSES[activeIssue.status].length === 0 && (
                    <p style={styles.muted}>
                        This review is in a terminal status and cannot be transitioned further.
                    </p>
                )}

                {actionError && (
                    <p role="alert" style={styles.actionError}>
                        {actionError}
                    </p>
                )}
              </section>

              <section style={styles.section}>
                <h3 style={styles.sectionTitle}>Comments</h3>

                <form onSubmit={(event) => void handleCommentSubmit(event)}>
                    <label htmlFor="review-comment" style={styles.detailLabel}>
                        Add an investigation comment
                    </label>

                    <textarea
                        id="review-comment"
                        value={commentText}
                        onChange={(event) => setCommentText(event.target.value)}
                        maxLength={5000}
                        rows={4}
                        placeholder="Record findings, context, or the next action..."
                        style={styles.commentInput}
                        disabled={commentSubmitting}
                    />

                    <div style={styles.actionRow}>
                        <span style={styles.muted}>
                            {commentText.length}/5000 characters
                        </span>

                        <button
                            type="submit"
                            style={styles.primaryButton}
                            disabled={commentSubmitting || !commentText.trim()}
                        >
                            {commentSubmitting ? "Submitting..." : "Add comment"}
                        </button>
                    </div>
                </form>

                {timelineLoading && (
                    <p role="status" style={styles.muted}>
                        Loading comments and activity...
                    </p>
                )}

                {timelineError && (
                    <div>
                        <p role="alert" style={styles.actionError}>{timelineError}</p>
                        <button
                            type="button"
                            style={styles.secondaryButton}
                            onClick={() => setTimelineReload((count) => count + 1)}
                        >
                            Retry loading activity
                        </button>
                    </div>
                )}

                {!timelineLoading && !timelineError && (
                    <div style={styles.stack}>
                        {comments.length === 0 ? (
                            <p style={styles.muted}>No comments yet.</p>
                        ) : (
                            comments.map((comment) => (
                                <article key={comment.id} style={styles.record}>
                                    <p style={styles.detailValue}>
                                        {comment.comment || "Comment unavailable"}
                                    </p>
                                    <p style={styles.muted}>
                                        {comment.author_id 
                                            ? `Author: ${comment.author_id} · `
                                            : ""
                                        }
                                        {new Date(comment.created_at).toLocaleString()}
                                    </p>
                                </article>
                            ))
                        )}
                    </div>
                )}
              </section>

              <section style={styles.section}>
                <h3 style={styles.sectionTitle}>Activity history</h3>

                {timelineLoading ? (
                    <p style={styles.muted}>Loading activity history...</p>
                ) : timelineError ? (
                    <p style={styles.muted}>
                        Activity history could not be loaded. Use the retry control above.
                    </p>
                ): activities.length === 0 ? (
                    <p style={styles.muted}>No activity recorded yet.</p>
                ) : (
                    <div style={styles.stack}>
                        {activities.map((activity) => (
                            <article key={activity.id} style={styles.record}>
                                <strong style={styles.detailValue}>
                                    {formatLabel(activity.activity_type)}
                                </strong>
                                {activity.comment && (
                                    <p style={styles.muted}>{activity.comment}</p>
                                )}
                                <p style={styles.muted}>
                                    {new Date(activity.created_at).toLocaleString()}
                                </p>
                                {Object.keys(activity.metadata ?? {}).length > 0 && (
                                    <StructuredDetails 
                                        title="Activity metadata"
                                        value={activity.metadata}
                                    />
                                )}
                            </article>
                        ))}
                    </div>
                )}
              </section>
              
              <section style={styles.section}>
                <h3 style={styles.sectionTitle}>Issue assessment</h3>
                <div style={styles.detailGrid}>
                  <div style={styles.detailItem}>
                    <span style={styles.detailLabel}>Severity</span>
                    <span style={styles.detailValue}>
                      {activeIssue.severity}
                    </span>
                  </div>
                  <div style={styles.detailItem}>
                    <span style={styles.detailLabel}>Status</span>
                    <span style={styles.detailValue}>
                      {formatLabel(activeIssue.status)}
                    </span>
                  </div>
                  <div style={styles.detailItem}>
                    <span style={styles.detailLabel}>Metric</span>
                    <span style={styles.detailValue}>
                      {activeIssue.metric}
                    </span>
                  </div>
                  <div style={styles.detailItem}>
                    <span style={styles.detailLabel}>Observed value</span>
                    <span style={styles.detailValue}>
                      {formatValue(activeIssue.observed_value)}
                    </span>
                  </div>
                  <div style={styles.detailItem}>
                    <span style={styles.detailLabel}>Threshold</span>
                    <span style={styles.detailValue}>
                      {formatValue(activeIssue.threshold)}
                    </span>
                  </div>
                  <div style={styles.detailItem}>
                    <span style={styles.detailLabel}>Assigned to</span>
                    <span style={styles.detailValue}>
                      {activeIssue.assigned_to || "Unassigned"}
                    </span>
                  </div>
                </div>

                {activeIssue.recommendations.length > 0 && (
                  <div style={styles.subsection}>
                    <h4 style={styles.subsectionTitle}>
                      Recommendations
                    </h4>
                    <ul style={styles.list}>
                      {activeIssue.recommendations.map(
                        (recommendation, index) => (
                          <li key={index}>
                            {typeof recommendation === "string"
                                ? recommendation
                                : JSON.stringify(recommendation)
                            }
                          </li>
                        ),
                      )}
                    </ul>
                  </div>
                )}

                {Object.keys(activeIssue.evidence).length > 0 && (
                  <div style={styles.subsection}>
                    <h4 style={styles.subsectionTitle}>Issue evidence</h4>
                    <DetailGrid data={activeIssue.evidence} />
                  </div>
                )}
              </section>

              <section style={styles.section}>
                <h3 style={styles.sectionTitle}>Order details</h3>
                {order ? (
                  <DetailGrid
                    data={order as unknown as Record<string, unknown>}
                  />
                ) : (
                  <p style={styles.muted}>
                    Order details were not returned by the service.
                  </p>
                )}
              </section>

              <StructuredDetails
                title={`Execution fills (${investigation.fills.length})`}
                value={investigation.fills}
              />

              <StructuredDetails
                title="Transaction cost analysis"
                value={investigation.tca}
              />

              <div style={styles.notice}>
                <CheckCircle2 size={17} aria-hidden="true" />
                Investigation data is sourced from the selected review's
                backend response.
              </div>
            </>
          )}
        </div>

        <footer style={styles.footer}>
          <span style={styles.footerMeta}>
            <Clock3 size={15} aria-hidden="true" />
            Created {new Date(activeIssue.created_at).toLocaleString()}
          </span>
          <button
            type="button"
            onClick={onClose}
            style={styles.primaryButton}
          >
            Close investigation
          </button>
        </footer>
      </section>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  backdrop: {
    position: "fixed",
    inset: 0,
    zIndex: 1000,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
    background: "rgba(15, 23, 42, 0.55)",
  },
  dialog: {
    display: "flex",
    flexDirection: "column",
    width: "min(960px, 100%)",
    maxHeight: "90vh",
    overflow: "hidden",
    background: "var(--surface, #ffffff)",
    color: "var(--text-primary, #172033)",
    border: "1px solid var(--border, #e2e8f0)",
    borderRadius: 16,
    boxShadow: "0 24px 80px rgba(15, 23, 42, 0.25)",
  },
  header: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 16,
    padding: 24,
    borderBottom: "1px solid var(--border, #e2e8f0)",
  },
  eyebrow: {
    margin: "0 0 8px",
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: "0.12em",
    color: "var(--text-muted, #64748b)",
  },
  title: {
    margin: "0 0 8px",
    fontSize: 21,
    lineHeight: 1.35,
    fontWeight: 650,
  },
  closeButton: {
    display: "grid",
    placeItems: "center",
    width: 36,
    height: 36,
    flexShrink: 0,
    border: "1px solid var(--border, #e2e8f0)",
    borderRadius: 9,
    background: "transparent",
    color: "inherit",
    cursor: "pointer",
  },
  body: {
    padding: 24,
    overflowY: "auto",
  },
  section: {
    marginBottom: 24,
    paddingBottom: 22,
    borderBottom: "1px solid var(--border, #e2e8f0)",
  },
  sectionTitle: {
    margin: "0 0 16px",
    fontSize: 15,
    fontWeight: 650,
  },
  subsection: {
    marginTop: 20,
  },
  subsectionTitle: {
    margin: "0 0 10px",
    fontSize: 13,
    fontWeight: 650,
  },
  detailGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: 14,
  },
  detailItem: {
    display: "flex",
    flexDirection: "column",
    gap: 5,
    minWidth: 0,
  },
  detailLabel: {
    fontSize: 12,
    color: "var(--text-muted, #64748b)",
  },
  detailValue: {
    fontSize: 13,
    fontWeight: 550,
    overflowWrap: "anywhere",
  },
  stack: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  record: {
    padding: 14,
    border: "1px solid var(--border, #e2e8f0)",
    borderRadius: 10,
  },
  actionRow: {
    display: "flex",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 12,
  },
  actionError: {
    marginTop: 12,
    color: "#b91c1c",
    fontSize: 13,
  },
  commentInput: {
    display: "block",
    width: "100%",
    boxSizing: "border-box",
    marginTop: 8,
    padding: 12,
    border: "1px solid var(--border, #e2e8f0)",
    borderRadius: 8,
    background: "var(--surface, #ffffff)",
    color: "inherit",
    font: "inherit",
    resize: "vertical",
  },
  list: {
    margin: 0,
    paddingLeft: 20,
    fontSize: 13,
    lineHeight: 1.7,
  },
  muted: {
    margin: "6px 0 0",
    fontSize: 12,
    color: "var(--text-muted, #64748b)",
    overflowWrap: "anywhere",
  },
  feedback: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: 20,
    fontSize: 13,
  },
  error: {
    display: "flex",
    alignItems: "flex-start",
    gap: 12,
    padding: 16,
    border: "1px solid #fecaca",
    borderRadius: 10,
    color: "#b91c1c",
    fontSize: 13,
  },
  notice: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginTop: 4,
    fontSize: 12,
    color: "var(--text-muted, #64748b)",
  },
  footer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: 12,
    padding: "16px 24px",
    borderTop: "1px solid var(--border, #e2e8f0)",
  },
  footerMeta: {
    display: "flex",
    alignItems: "center",
    gap: 7,
    fontSize: 12,
    color: "var(--text-muted, #64748b)",
  },
  primaryButton: {
    padding: "10px 15px",
    border: 0,
    borderRadius: 8,
    background: "var(--accent, #2563eb)",
    color: "#ffffff",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
  },
  secondaryButton: {
    marginTop: 8,
    padding: "7px 10px",
    border: "1px solid #fecaca",
    borderRadius: 7,
    background: "#ffffff",
    color: "#b91c1c",
    fontSize: 12,
    cursor: "pointer",
  },
};
