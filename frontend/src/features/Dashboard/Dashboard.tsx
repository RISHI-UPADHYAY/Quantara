import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity,
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Bell,
  BookOpen,
  ChevronDown,
  CircleHelp,
  Clock3,
  Database,
  FileCheck2,
  FileText,
  LayoutDashboard,
  LineChart,
  LogOut,
  Moon,
  MoreHorizontal,
  PanelLeftClose,
  PlayCircle,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Sun,
  Users,
  WalletCards,
  X,
  Zap,
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import {
  getOrganizations,
  getProjects,
  type Organization,
  type Project,
} from "../../services/workspaceService";
import {
  getPilotWorkspaceOverview,
  type PilotWorkspaceOverview,
} from "../../services/workspaceService";
import {
  listReviewIssues,
  type ReviewIssue,
  type ReviewStatus,
} from "../../services/reviewQueueService";
import { getApiErrorMessage } from "../../services/api";
import ReviewInvestigationPanel from "./ReviewInvestigationPanel";
import "./Dashboard.css";

const navGroups = [
  {
    label: "WORKSPACE",
    items: [
      { icon: LayoutDashboard, label: "Overview", active: true },
      { icon: BarChart3, label: "Orders & Fills" },
      { icon: LineChart, label: "Execution Analysis" },
      { icon: FileCheck2, label: "Review Queue" },
      { icon: Activity, label: "Analysis Runs" },
    ],
  },
  {
    label: "DATA",
    items: [
      { icon: Database, label: "Datasets" },
      { icon: ShieldCheck, label: "Data Quality" },
      { icon: RefreshCw, label: "Dataset Versions" },
    ],
  },
  {
    label: "RESEARCH & ANALYTICS",
    items: [
      { icon: BookOpen, label: "Research Workspace" },
      { icon: WalletCards, label: "Portfolio & Risk" },
      { icon: SlidersHorizontal, label: "Derivatives Analytics" },
      { icon: Sparkles, label: "AI Research Assistant" },
    ],
  },
  {
    label: "REPORTS",
    items: [{ icon: FileText, label: "Reports" }],
  },
  {
    label: "ADMINISTRATION",
    items: [
      { icon: Users, label: "Organization" },
      { icon: Settings2, label: "Settings" },
    ],
  },
];

type Accent = "blue" | "amber" | "green" | "slate";

function MetricCard({
  label,
  value,
  detail,
  accent = "slate",
  icon: Icon,
}: {
  label: string;
  value: string;
  detail: string;
  accent?: Accent;
  icon: typeof Activity;
}) {
  return (
    <article className="metric-card">
      <div className="metric-card-top">
        <p className="metric-label">{label}</p>
        <span className={`metric-icon metric-${accent}`}>
          <Icon aria-hidden="true" />
        </span>
      </div>
      <p className="metric-value">{value}</p>
      <p className="metric-detail">{detail}</p>
    </article>
  );
}

function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    try {
      return localStorage.getItem("quantara-theme") === "dark"
        ? "dark"
        : "light";
    } catch {
      return "light";
    }
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;

    try {
      localStorage.setItem("quantara-theme", theme);
    } catch {
      // Theme switching still works if browser storage is unavailable.
    }
  }, [theme]);

  return (
    <button
      className="dashboard-icon-button theme-toggle"
      type="button"
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
      title={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
      onClick={() =>
        setTheme((current) => (current === "light" ? "dark" : "light"))
      }
    >
      {theme === "light" ? (
        <Moon aria-hidden="true" />
      ) : (
        <Sun aria-hidden="true" />
      )}
    </button>
  );
}

function ExecutionTrendChart() {
  return (
    <div
      className="trend-chart"
      role="status"
      aria-label="Historical execution trend unavailable"
    >
      <p>Historical trend data is not available from this overview.</p>
    </div>
  );
}

function formatCount(value: number | null | undefined): string {
  return new Intl.NumberFormat("en-US").format(value ?? 0);
}

function formatPercent(value: number | null | undefined): string {
  return value == null ? "-" : `${value.toFixed(1)}%`;
}

function formatReviewDate(value: string): string {
  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "-"
    : date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
}

export default function Dashboard() {
  const [collapsed, setCollapsed] = useState(false);
  const [range, setRange] = useState("Last 30 days");
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [workspaceLoading, setWorkspaceLoading] = useState(true);
  const [workspaceError, setWorkspaceError] = useState("");
  const [showWorkspacePicker, setShowWorkspacePicker] = useState(false);
  const [overview, setOverview] = useState<PilotWorkspaceOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [overviewError, setOverviewError] = useState("");
  const [reviewActionMessage, setReviewActionMessage] = useState("");
  const [reviewIssues, setReviewIssues] = useState<ReviewIssue[]>([]);
  const [reviewQueueLoading, setReviewQueueLoading] = useState(false);
  const [reviewQueueError, setReviewQueueError] = useState<string | null>(null);
  const [reviewQueueReload, setReviewQueueReload] = useState(0);
  const [reviewStatusFilter, setReviewStatusFilter] = useState<ReviewStatus | "ALL">("ALL");
  const [selectedReviewIssue, setSelectedReviewIssue] = useState<ReviewIssue | null>(null);

  const selectedOrganization = organizations.find(
    (organization) => organization.id === selectedOrganizationId,
  );

  const selectedProject = projects.find(
    (project) => project.id === selectedProjectId,
  );

  useEffect(() => {
    let cancelled = false;

    async function loadOrganizations() {
      setWorkspaceLoading(true);
      setWorkspaceError("");

      try {
        const result = await getOrganizations();

        if (cancelled)
          return;

        setOrganizations(result);
        setSelectedOrganizationId(result[0]?.id ?? "");
      } catch (erorr) {
        if (!cancelled) {
          setWorkspaceError(
            getApiErrorMessage(erorr, "Unable to load organizations."),
          );
        }
      } finally {
        if (!cancelled) {
          setWorkspaceLoading(false);
        }
      }
    }

    void loadOrganizations();

    return () => {
      cancelled = true
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadProjects() {
      setProjects([]);
      setSelectedProjectId("");
      setWorkspaceError("");

      if (!selectedOrganizationId)
        return;

      try {
        const result = await getProjects(selectedOrganizationId);

        if (cancelled)
          return;

        setProjects(result);
        setSelectedProjectId(result[0]?.id ?? "");

        if (result.length === 0) {
          setWorkspaceError(
            "This organization has no projects yet.",
          );
        }
      } catch (error) {
        if (!cancelled) {
          setWorkspaceError(
            getApiErrorMessage(error, "Unable to load projects."),
          );
        }
      }
    }

    void loadProjects();

    return () => {
      cancelled = true;
    };
  }, [selectedOrganizationId]);

  useEffect(() => {
    let cancelled = false;

    async function loadOverview() {
      if (!selectedOrganizationId || !selectedProjectId) {
        setOverview(null);
        setOverviewLoading(false);
        return;
      }

      setOverviewLoading(true);
      setOverviewError("");
      setOverview(null);

      try {
        const days =
          range === "Last 7 days"
            ? 7
            : range === "Last 90 days"
              ? 90
              : 30;

        const end = new Date();
        const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000);

        const result = await getPilotWorkspaceOverview(
          selectedOrganizationId,
          selectedProjectId,
          {
            startTime: start.toISOString(),
            endTime: end.toISOString(),
          },
        );

        if (!cancelled) {
          setOverview(result);
        }
      } catch (error) {
        if (!cancelled) {
          setOverviewError(
            getApiErrorMessage(error, "Unable to load workspace overview."),
          );
        }
      } finally {
        if (!cancelled) {
          setOverviewLoading(false);
        }
      }
    }

    void loadOverview();

    return () => {
      cancelled = true;
    };
  }, [selectedOrganizationId, selectedProjectId, range]);

  useEffect(() => {
    if (!selectedOrganizationId || !selectedProjectId) {
      setSelectedReviewIssue(null);
      setReviewIssues([]);
      setReviewQueueError(null);
      return;
    }

    let cancelled = false;

    async function loadReviewQueue () {
      setReviewQueueLoading(true);
      setReviewQueueError(null);

      try {
        const response = await listReviewIssues (
          selectedOrganizationId,
          selectedProjectId,
          {
            limit: 100,
            offset: 0,
            ...(reviewStatusFilter !== "ALL"
              ? { status: reviewStatusFilter }
              : {}
            ),
          },
        );

        if (!cancelled) {
          setReviewIssues(response.items);
        } 
      } catch {
        if (!cancelled) {
          setReviewQueueError(
            "Unable to load review issues. Check your connection and permissions, then retry.",
          );
        }
      } finally {
        if (!cancelled) {
          setReviewQueueLoading(false);
        }
      }
    }

    void loadReviewQueue();

    return () => {
      cancelled = true;
    }
  }, [
    selectedOrganizationId,
    selectedProjectId,
    reviewStatusFilter,
    reviewQueueReload,
  ]);

  useEffect(() => {
    setSelectedReviewIssue(null);
  }, [selectedOrganizationId, selectedProjectId]);

  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const displayName = user?.name?.trim() || "Quantara User";
  const initials =
    displayName
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "QU";

  const handleLogout = async () => {
    setShowProfileMenu(false);
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className={`app-shell ${collapsed ? "is-collapsed" : ""}`}>
      <aside className={`sidebar ${collapsed ? "sidebar-collapsed" : ""}`}>
        <div className="brand-row">
          <a className="dashboard-brand" href="/" aria-label="Quantara home">
            <span className="brand-mark">Q</span>
            {!collapsed && (
              <span className="brand-copy">
                <span className="brand-name">quantara</span>
                <span className="brand-sub">INSTITUTIONAL INTELLIGENCE</span>
              </span>
            )}
          </a>

          <button
            className="collapse-btn"
            type="button"
            onClick={() => setCollapsed((value) => !value)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <PanelLeftClose aria-hidden="true" />
          </button>
        </div>

        <button
          className="workspace-switcher"
          type="button"
          onClick={() => setShowWorkspacePicker((value) => !value)}
          aria-expanded={showWorkspacePicker}
          aria-label="Select organization and project"
        >
          <span className="workspace-dot">N</span>
          {!collapsed && (
            <span className="workspace-copy">
              <span className="workspace-name">
                {
                  workspaceLoading
                    ? "Loading organizations..."
                    : selectedOrganization?.name ?? "Select organization"
                }
              </span>
              <span className="workspace-project">
                {
                  selectedProject?.name ?? "Select project"
                }
                <ChevronDown aria-hidden="true" />
              </span>
            </span>
          )}
        </button>

        {showWorkspacePicker && !collapsed && (
          <div
            className="profile-popover"
            style={{
              left: 12,
              right: 12,
              top: 82,
              bottom: "auto",
              width: "auto",
            }}
          >
            <strong>Select workspace</strong>

            <label>
              <span>Organization</span>
              <select
                value={selectedOrganizationId}
                onChange={(event) =>
                  setSelectedOrganizationId(event.target.value)
                }
                disabled={workspaceLoading || organizations.length === 0}
                style={{ width: "100%", padding: 8 }}
              >
                {organizations.length === 0 && (
                  <option value="">No organizations available</option>
                )}

                {organizations.map((organization) => (
                  <option key={organization.id} value={organization.id}>
                    {organization.name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Project</span>
              <select
                value={selectedProjectId}
                onChange={(event) => setSelectedProjectId(event.target.value)}
                disabled={projects.length === 0}
                style={{ width: "100%", padding: 8 }}
              >
                {projects.length === 0 && (
                  <option value="">No projects available</option>
                )}

                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>

            {workspaceError && (
              <span role="alert">{workspaceError}</span>
            )}

            <button
              type="button"
              onClick={() => setShowWorkspacePicker(false)}
            >
              Done
            </button>
          </div>
        )}

        <nav className="nav-scroll" aria-label="Workspace navigation">
          {navGroups.map((group) => (
            <div className="nav-group" key={group.label}>
              {!collapsed && (
                <div className="nav-group-label">{group.label}</div>
              )}

              {group.items.map((item) => {
                const Icon = item.icon;
                const label = item.label;
                const active = "active" in item ? item.active : false;
                const count = "count" in item && item.count === "string" ? item.count : undefined;

                return (
                  <button
                    className={`nav-item ${active ? "nav-item-active" : ""}`}
                    key={label}
                    type="button"
                    title={collapsed ? label : undefined}
                    onClick={() => {
                      if (label === "Review Queue") {
                        document
                          .getElementById("review-priorities")
                          ?.scrollIntoView({ behavior: "smooth" });
                      } else if (label === "Data Quality") {
                        document
                          .getElementById("data-health")
                          ?.scrollIntoView({ behavior: "smooth" });
                      } else if (label === "Overview") {
                        window.scrollTo({ top: 0, behavior: "smooth" });
                      }
                    }}
                  >
                    <Icon aria-hidden="true" />
                    {!collapsed && (
                      <>
                        <span>{label}</span>
                        {count !== undefined && (<span className="nav-count">{count}</span>)}
                      </>
                    )}
                  </button>
                )
              })}

            </div>
          ))}
        </nav>

        {!collapsed && (
          <div className="sidebar-footer">
            <div className="pilot-badge">
              <span className="status-dot" />
              Demo environment <span className="pilot-tag">PILOT</span>
            </div>

            <button
              className="sidebar-user"
              type="button"
              onClick={() => setShowProfileMenu((value) => !value)}
            >
              <span className="avatar avatar-small">{initials}</span>
              <span className="sidebar-user-copy">
                <span className="user-name">{displayName}</span>
                <span className="user-role">{user?.email || "Workspace member"}</span>
              </span>
              <MoreHorizontal aria-hidden="true" />
            </button>

            {showProfileMenu && (
              <div className="profile-popover">
                <strong>{displayName}</strong>
                <span>{user?.email}</span>
                <button type="button" onClick={handleLogout}>
                  <LogOut aria-hidden="true" /> Sign out
                </button>
              </div>
            )}
          </div>
        )}
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>{selectedOrganization?.name ?? "Workspace"}</span>
            <span className="crumb-separator">/</span>
            <span>{selectedProject?.name ?? "No project selected"}</span>
            <span className="crumb-separator">/</span>
            <strong>Overview</strong>
          </div>

          <div className="topbar-actions">
            <button
              className="command-btn"
              type="button"
              onClick={() => setSearchOpen((value) => !value)}
            >
              <Search aria-hidden="true" />
              <span>Search workspace</span>
              <kbd>Ctrl K</kbd>
            </button>

            <ThemeToggle />

            <div className="notification-wrap">
              <button
                className="dashboard-icon-button notification-button"
                type="button"
                onClick={() => setShowNotifications((value) => !value)}
                aria-label="Notifications"
                aria-expanded={showNotifications}
              >
                <Bell aria-hidden="true" />
                <span className="notification-dot" />
              </button>

              {showNotifications && (
                <div className="notification-popover">
                  <div className="popover-title">
                    Notifications <span>3 new</span>
                  </div>
                  <div className="notification-item">
                    <span className="severity-dot red" />
                    <div>
                      <strong>Analysis failure</strong>
                      <p>3 orders missing benchmark data</p>
                    </div>
                  </div>
                  <div className="notification-item">
                    <span className="severity-dot amber" />
                    <div>
                      <strong>Review assigned</strong>
                      <p>High slippage review · AAPL</p>
                    </div>
                  </div>
                  <div className="notification-item">
                    <span className="severity-dot blue" />
                    <div>
                      <strong>Dataset updated</strong>
                      <p>US Equities v2024.11.28</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <button
              className="profile-trigger"
              type="button"
              onClick={() => setShowProfileMenu((value) => !value)}
              aria-label="Open account menu"
            >
              <span className="avatar avatar-header">{initials}</span>
              <ChevronDown aria-hidden="true" />
            </button>

            {showProfileMenu && (
              <div className="top-profile-popover">
                <strong>{displayName}</strong>
                <span>{user?.email}</span>
                <button type="button" onClick={handleLogout}>
                  <LogOut aria-hidden="true" /> Sign out
                </button>
              </div>
            )}
          </div>
        </header>

        {searchOpen && (
          <div className="workspace-search">
            <Search aria-hidden="true" />
            <input
              autoFocus
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search this workspace..."
              aria-label="Search this workspace"
              onKeyDown={(event) => {
                if (event.key === "Escape") setSearchOpen(false);
                if (event.key === "Enter") {
                  const query = searchQuery.toLowerCase();
                  if (query.includes("review")) {
                    document
                      .getElementById("review-priorities")
                      ?.scrollIntoView({ behavior: "smooth" });
                    setSearchOpen(false);
                  } else if (query.includes("health") || query.includes("data")) {
                    document
                      .getElementById("data-health")
                      ?.scrollIntoView({ behavior: "smooth" });
                    setSearchOpen(false);
                  }
                }
              }}
            />
            <button
              type="button"
              onClick={() => {
                setSearchOpen(false);
                setSearchQuery("");
              }}
              aria-label="Close search"
            >
              <X aria-hidden="true" />
            </button>
          </div>
        )}

        <div className="page-content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                <span className="live-dot" />
                PILOT WORKSPACE <span className="eyebrow-divider">·</span>
                EXECUTION INTELLIGENCE
              </div>
              <h1>Workspace Overview</h1>
              <p>
                Execution intelligence, analysis coverage, and review
                priorities for your workspace.
              </p>
            </div>

            <div className="heading-actions">
              <label className="date-btn">
                <Clock3 aria-hidden="true" />
                <select
                  value={range}
                  onChange={(event) => setRange(event.target.value)}
                  aria-label="Reporting range"
                >
                  <option>Last 7 days</option>
                  <option>Last 30 days</option>
                  <option>Last 90 days</option>
                </select>
                <ChevronDown aria-hidden="true" />
              </label>

              <button
                className="primary-btn"
                type="button"
                onClick={() =>
                  document
                    .getElementById("review-priorities")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
              >
                <Zap aria-hidden="true" />
                Review exceptions{" "}
                <span className="btn-count">
                  {formatCount(overview?.exceptions.open)}
                </span>
              </button>
            </div>
          </div>

          <div className="context-bar">
            <div className="context-item">
              <Database aria-hidden="true" />
              <div>
                <span>Active dataset</span>
                <strong>
                  {
                    overview?.market_data.version != null
                      ? `Dataset version ${overview.market_data.version}`
                      : "No market-data version selected"
                  }
                </strong>
              </div>
              <ChevronDown aria-hidden="true" />
            </div>

            <div className="context-divider" />

            <div className="context-item">
              <Clock3 aria-hidden="true" />
              <div>
                <span>Reporting period</span>
                <strong>
                  {range}
                </strong>
              </div>
              <ChevronDown aria-hidden="true" />
            </div>

            <div className="context-spacer" />

            <span className="context-status">
              <span
                className={`status-dot ${overviewError ? "" : overviewLoading ? "" : "green-dot"
                  }`}
              />
              {
                overviewError
                  ? "Data unavailable"
                  : overviewLoading
                    ? "Syncing workspace..."
                    : overview
                      ? "Workspace data loaded"
                      : "No workspace selected"
              }
            </span>
          </div>

          {overviewError && (
            <div className="workspace-error" role="alert">
              {overviewError}
            </div>
          )}

          <section className="section">
            <div className="section-heading">
              <div>
                <h2>Operational summary</h2>
                <p>
                  Order activity and analysis coverage across the selected
                  period.
                </p>
              </div>
              <button className="text-btn" type="button">
                View orders <ArrowUpRight aria-hidden="true" />
              </button>
            </div>

            <div className="metrics-grid">
              <MetricCard
                label="Total orders"
                value={overviewLoading ? "-" : formatCount(overview?.execution.orders)}
                detail={overviewError || (overview ? "Orders in selected period" : "Awaiting workspace data")}
                accent="blue"
                icon={BarChart3}
              />
              <MetricCard
                label="Filled orders"
                value={overviewLoading ? "-" : formatCount(overview?.execution.filled_orders)}
                detail={`${formatPercent(
                  overview?.execution.orders
                    ? (overview.execution.filled_orders / overview.execution.orders) * 100
                    : 0,
                )} of total orders`}
                accent="green"
                icon={FileCheck2}
              />
              <MetricCard
                label="Partially filled"
                value={overviewLoading ? "-" : formatCount(overview?.execution.partially_filled_orders)}
                detail={`${formatPercent(
                  overview?.execution.orders
                    ? (overview.execution.partially_filled_orders / overview.execution.orders) * 100
                    : 0,
                )} of total orders`}
                accent="amber"
                icon={Activity}
              />
              <MetricCard
                label="Unfilled orders"
                value={overviewLoading ? "-" : formatCount(overview?.execution.unfilled_orders)}
                detail={`${formatPercent(
                  overview?.execution.orders
                    ? (overview.execution.unfilled_orders / overview.execution.orders) * 100
                    : 0,
                )} of total orders`}
                accent="slate"
                icon={X}
              />
              <MetricCard
                label="Analysis complete"
                value={overviewLoading ? "-" : formatCount(overview?.execution.analyzed_orders)}
                detail={`${formatPercent(overview?.execution.tca_coverage_percentage)} analysis coverage`}
                accent="blue"
                icon={LineChart}
              />
              <MetricCard
                label="Requires review"
                value={overviewLoading ? "-" : formatCount(overview?.exceptions.open)}
                detail={`${formatCount(overview?.exceptions.critical)} critical · ${formatCount(overview?.exceptions.high)} high`}
                accent="amber"
                icon={AlertCircle}
              />
            </div>
          </section>

          <div className="content-grid">
            <section className="panel execution-panel">
              <div className="panel-header">
                <div>
                  <h2>Execution analysis</h2>
                  <p>
                    Transaction cost analysis coverage for eligible orders.
                  </p>
                </div>
                <button className="more-btn" type="button" aria-label="More options">
                  <MoreHorizontal aria-hidden="true" />
                </button>
              </div>

              <div className="analysis-body">
                <div className="coverage-chart">
                  <div
                    className="donut"
                    style={{
                      background: `conic-gradient(
                      var(--accent, #2563eb) ${Math.min(100, Math.max(0, overview?.execution.tca_coverage_percentage ?? 0))
                        }%,
                      var(--border, #e5e7eb) 0
                      )`,
                    }}
                  >
                    <div className="donut-center">
                      <strong>
                        {formatPercent(overview?.execution.tca_coverage_percentage)}
                      </strong>
                      <span>eligible analyzed</span>
                    </div>
                  </div>
                  <div className="chart-caption">
                    <div>
                      <span className="legend-dot analyzed" /> Analyzed
                      <strong>
                        {formatCount(overview?.execution.analyzed_orders)}
                      </strong>
                    </div>
                    <div>
                      <span className="legend-dot failed" /> Failed
                      <strong>
                        {formatCount(overview?.execution.failed_orders)}
                      </strong>
                    </div>
                    <div>
                      <span className="legend-dot excluded" /> Excluded
                      <strong>-</strong>
                    </div>
                  </div>
                </div>

                <div className="analysis-stats">
                  <div className="analysis-stat">
                    <span>Eligible orders</span>
                    <strong>
                      {formatCount(overview?.execution.tca_requested_orders)}
                    </strong>
                    <small>
                      {formatPercent(overview?.execution.tca_coverage_percentage)} analyzed
                    </small>
                  </div>
                  <div className="analysis-stat">
                    <span>Analysis failures</span>
                    <strong className="text-red">
                      {formatCount(overview?.execution.failed_orders)}
                    </strong>
                    <small>
                      {
                        overview?.execution.tca_requested_orders
                          ? formatPercent(
                            (overview.execution.failed_orders / overview.execution.tca_requested_orders) * 100,
                          ) + " of eligible orders"
                          : "Eligible-order denominator unavailable"
                      } <ArrowDownRight aria-hidden="true" />
                    </small>
                  </div>
                  <div className="failure-note">
                    <AlertCircle aria-hidden="true" />
                    <div>
                      <strong>Primary failure reason</strong>
                      <p>
                        Failure-reason breakdown is not available from the workspace overview.
                      </p>
                      <button type="button" onClick={() => document.getElementById("data-health")?.scrollIntoView({ behavior: "smooth" })}>
                        Inspect data quality <ArrowUpRight aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="panel-footer">
                <span>
                  <CircleHelp aria-hidden="true" /> Denominator: eligible
                  orders with complete market data and valid timestamps.
                </span>
                <button className="text-btn" type="button">
                  View analysis runs <ArrowUpRight aria-hidden="true" />
                </button>
              </div>
            </section>

            <section className="panel trend-panel">
              <div className="panel-header">
                <div>
                  <h2>Execution quality trend</h2>
                  <p>Weighted implementation shortfall · percentage</p>
                </div>
                <span className="date-pill">30D <ChevronDown aria-hidden="true" /></span>
              </div>

              <div className="trend-value">
                <strong>
                  {
                    overview?.execution.weighted_shortfall_percentage == null
                      ? "-"
                      : `${(overview.execution.weighted_shortfall_percentage * 100).toFixed(1)} bps`
                  }
                </strong>
                <span className="muted-copy">
                  Historical comparison unavailable
                </span>
              </div>

              <ExecutionTrendChart />

              <div className="trend-foot">
                <span>
                  <span className="legend-dot analyzed" /> Median IS
                </span>
                <span className="trend-foot-note">
                  Historical trend data unavailable
                </span>
              </div>
            </section>
          </div>

          <div className="bottom-grid">
            <section className="panel review-panel" id="review-priorities">
              <div className="panel-header">
                <div>
                  <h2>Review priorities</h2>
                  <p>Exceptions that need a decision or evidence.</p>
                </div>
                <button className="text-btn" type="button">
                  Open queue <ArrowUpRight aria-hidden="true" />
                </button>
              </div>

              <div className="review-list">
                <div className="review-summary">
                  <label htmlFor="review-status-filter">Status</label>
                  <select 
                    id="review-status-filter"
                    value={reviewStatusFilter}
                    onChange={(event) => setReviewStatusFilter(
                      event.target.value as ReviewStatus | "ALL",
                    )}
                  >
                    <option value="ALL">All statuses</option>
                    <option value="OPEN">Open</option>
                    <option value="ACKNOWLEDGED">Acknowledged</option>
                    <option value="IN_REVIEW">In review</option>
                    <option value="RESOLVED">Resolved</option>
                    <option value="IGNORED">Ignored</option>
                  </select>

                  <button
                    className="text-btn"
                    type="button"
                    disabled={reviewQueueLoading}
                    onClick={() => setReviewQueueReload((value) => value + 1)}
                  >
                    {reviewQueueLoading ? "Refreshing..." : "Refresh queue"}
                  </button>
                </div>

                {reviewQueueError && (
                  <div role="alert" className="review-summary">
                    <span>{reviewQueueError}</span>
                    <button
                      className="text-btn"
                      type="button"
                      onClick={() => setReviewQueueReload((value) => value + 1)}
                    >
                      Retry
                    </button>
                  </div>
                )}

                {reviewQueueLoading && reviewIssues.length === 0 && (
                  <p role="status">Loading review issues...</p>
                )}

                {!reviewQueueLoading &&
                  !reviewQueueError &&
                  reviewIssues.length === 0 && (
                    <p>No review issues found for this filter.</p>
                  )
                }

                {reviewIssues.map((issue) => {
                  const severity = issue.severity.toLowerCase();

                  return (
                    <div className="review-row" key={issue.id}>
                      <div
                        className={`priority-icon ${
                          ["critical", "high", "medium"].includes(severity)
                            ? severity
                            : "medium"
                        }`}
                      >
                        <AlertCircle aria-hidden="true" />
                      </div>

                      <div className="review-copy">
                        <strong>
                          {issue.message || issue.issue_code.replaceAll("_", " ")}
                        </strong>
                        <span>
                          {issue.metric} · Order {issue.order_id} ·{" "}
                          {formatReviewDate(issue.created_at)}
                        </span>
                      </div>

                      <span
                        className={`review-badge ${
                          ["critical", "high", "medium"].includes(severity)
                            ? `${severity}-badge`
                            : "medium-badge"
                        }`}
                      >
                        {issue.severity}
                      </span>

                      <span className="review-owner">
                        {issue.assigned_to ? "Assigned" : "Unassigned"}
                      </span>

                      <button
                        className="row-arrow"
                        type="button"
                        aria-label={`Review ${issue.issue_code}`}
                        title={`Status: ${issue.status}`}
                        onClick={() => {
                          setReviewActionMessage("");
                          setSelectedReviewIssue(issue);
                        }}
                      >
                        <ArrowUpRight aria-hidden="true" />
                      </button>
                    </div>
                  );
                })}
              </div>

              {reviewActionMessage && (
                <p role="status">{reviewActionMessage}</p>
              )}


              <div className="review-summary">
                <span>
                  <strong>{formatCount(overview?.exceptions.open)}</strong> open reviews
                </span>
                <span>
                  <strong>
                    {formatCount(
                      (overview?.exceptions.critical ?? 0) +
                      (overview?.exceptions.high ?? 0),
                    )}
                  </strong>{" "}
                  critical / high
                </span>
                <span>
                  <strong>
                    {formatCount(overview?.exceptions.acknowledged)}
                  </strong>{" "}
                  acknowledged
                </span>
                <span>
                  <strong>{formatCount(overview?.exceptions.in_review)}</strong>{" "}
                  in review
                </span>
              </div>
            </section>

            <section className="panel health-panel" id="data-health">
              <div className="panel-header">
                <div>
                  <h2>Data health</h2>
                  <p>Current dataset reliability and coverage.</p>
                </div>
                <button className="more-btn" type="button" aria-label="Data health options">
                  <MoreHorizontal aria-hidden="true" />
                </button>
              </div>

              <div className="health-status">
                <div className="health-ring">
                  <ShieldCheck aria-hidden="true" />
                </div>
                <div>
                  <strong>
                    {
                      overviewLoading
                        ? "Loading data health..."
                        : overviewError
                          ? "Data health unavailable"
                          : overview?.market_data.dataset_version_id
                            ? "Dataset version selected"
                            : "No dataset version selected"
                    }
                  </strong>
                  <span>
                    {
                      overview?.market_data.dataset_version_id
                        ? "Validation details are not available in this overview."
                        : "No validation timestamp available."
                    }
                  </span>
                </div>
              </div>

              <div className="health-items">
                <div>
                  <span>Timestamp coverage</span>
                  <strong>-</strong>
                  <span>Not provided by overview API</span>
                </div>

                <div>
                  <span>Instrument coverage</span>
                  <strong>-</strong>
                  <span>Not provided by overview API</span>
                </div>

                <div>
                  <span>Missing benchmark data</span>
                  <strong>-</strong>
                  <span>Detailed breakdown unavailable</span>
                </div>
              </div>

              <button
                className="outline-btn"
                type="button"
                onClick={() => document.getElementById("data-health")?.scrollIntoView({ behavior: "smooth" })}
              >
                Inspect dataset quality <ArrowUpRight aria-hidden="true" />
              </button>
            </section>
          </div>

          <section className="activity-section">
            <div className="section-heading">
              <div>
                <h2>Recent activity</h2>
                <p>Latest changes and actions across the workspace.</p>
              </div>
              <button className="text-btn" type="button">
                View all activity <ArrowUpRight aria-hidden="true" />
              </button>
            </div>

            <div className="activity-table">
              <div className="table-head">
                <span>ACTIVITY</span>
                <span>ACTOR</span>
                <span>TIME</span>
                <span>STATUS</span>
                <span />
              </div>

              <div className="activity-row">
                <div className="activity-name">
                  <span className="activity-icon blue">
                    <PlayCircle aria-hidden="true" />
                  </span>
                  <div>
                    <strong>Analysis run completed</strong>
                    <span>Execution quality · 6,274 orders analyzed</span>
                  </div>
                </div>
                <span>System</span>
                <span>8 min ago</span>
                <span className="status-tag success">Completed</span>
                <button className="row-arrow" type="button" aria-label="View analysis run">
                  <ArrowUpRight aria-hidden="true" />
                </button>
              </div>

              <div className="activity-row">
                <div className="activity-name">
                  <span className="activity-icon purple">
                    <Database aria-hidden="true" />
                  </span>
                  <div>
                    <strong>Dataset version published</strong>
                    <span>US Equities · v2024.11.28</span>
                  </div>
                </div>
                <span>J. Mitchell</span>
                <span>42 min ago</span>
                <span className="status-tag success">Published</span>
                <button className="row-arrow" type="button" aria-label="View dataset update">
                  <ArrowUpRight aria-hidden="true" />
                </button>
              </div>

              <div className="activity-row">
                <div className="activity-name">
                  <span className="activity-icon amber">
                    <FileCheck2 aria-hidden="true" />
                  </span>
                  <div>
                    <strong>Review decision recorded</strong>
                    <span>MSFT order #18402 · evidence attached</span>
                  </div>
                </div>
                <span>L. Chen</span>
                <span>1 hr ago</span>
                <span className="status-tag neutral">Resolved</span>
                <button className="row-arrow" type="button" aria-label="View review decision">
                  <ArrowUpRight aria-hidden="true" />
                </button>
              </div>
            </div>
          </section>

          <footer className="page-footer">
            <span>Quantara Pilot Workspace · Demo data only</span>
            <span>
              © 2026 Quantara <span className="footer-dot">·</span>{" "}
              <a href="#audit">Audit log</a> <span className="footer-dot">·</span>{" "}
              <a href="#help">Help center</a>
            </span>
          </footer>
        </div>

        {selectedReviewIssue &&
          selectedOrganizationId &&
          selectedProjectId && (
            <ReviewInvestigationPanel
              organizationId={selectedOrganizationId}
              projectId={selectedProjectId}
              issue={selectedReviewIssue}
              onClose={() => setSelectedReviewIssue(null)}
              onUpdated={(updatedIssue) => {
                setSelectedReviewIssue(updatedIssue);
                setReviewActionMessage(
                  `Review status updated to ${updatedIssue.status.replaceAll("_", " ")}.`,
                );
                setReviewQueueReload((value) => value + 1);
              }}
            />
          )
        }
      </main>
    </div>
  );
}