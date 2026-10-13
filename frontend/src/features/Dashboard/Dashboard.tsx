
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
import "./Dashboard.css";

const navGroups = [
  {
    label: "WORKSPACE",
    items: [
      { icon: LayoutDashboard, label: "Overview", active: true },
      { icon: BarChart3, label: "Orders & Fills" },
      { icon: LineChart, label: "Execution Analysis" },
      { icon: FileCheck2, label: "Review Queue", count: "12" },
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
    <div className="trend-chart">
      <div className="chart-y-axis">
        <span>0</span>
        <span>-3</span>
        <span>-6</span>
        <span>-9</span>
      </div>

      <div className="chart-area">
        <div className="grid-line one" />
        <div className="grid-line two" />
        <div className="grid-line three" />

        <svg
          viewBox="0 0 430 120"
          preserveAspectRatio="none"
          role="img"
          aria-label="Illustrative execution quality trend over November"
        >
          <defs>
            <linearGradient id="execution-area" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor="#2563eb" stopOpacity=".16" />
              <stop offset="1" stopColor="#2563eb" stopOpacity="0" />
            </linearGradient>
          </defs>

          <path
            d="M0 94 C25 88 32 78 56 84 S89 63 111 71 S142 53 166 62 S191 38 217 48 S244 35 272 44 S297 20 326 31 S350 13 378 24 S403 10 430 15 L430 120 L0 120Z"
            fill="url(#execution-area)"
          />
          <path
            d="M0 94 C25 88 32 78 56 84 S89 63 111 71 S142 53 166 62 S191 38 217 48 S244 35 272 44 S297 20 326 31 S350 13 378 24 S403 10 430 15"
            fill="none"
            stroke="#2563eb"
            strokeWidth="2.5"
          />
        </svg>

        <div className="chart-x-axis">
          <span>Nov 01</span>
          <span>Nov 08</span>
          <span>Nov 15</span>
          <span>Nov 22</span>
          <span>Nov 30</span>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [collapsed, setCollapsed] = useState(false);
  const [range, setRange] = useState("Last 30 days");
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
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

        <button className="workspace-switcher" type="button">
          <span className="workspace-dot">N</span>
          {!collapsed && (
            <span className="workspace-copy">
              <span className="workspace-name">Northstar Capital</span>
              <span className="workspace-project">
                Execution Pilot <ChevronDown aria-hidden="true" />
              </span>
            </span>
          )}
        </button>

        <nav className="nav-scroll" aria-label="Workspace navigation">
          {navGroups.map((group) => (
            <div className="nav-group" key={group.label}>
              {!collapsed && (
                <div className="nav-group-label">{group.label}</div>
              )}

              {group.items.map(({ icon: Icon, label, active, count }) => (
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
                      {count && <span className="nav-count">{count}</span>}
                    </>
                  )}
                </button>
              ))}
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
            <span>Northstar Capital</span>
            <span className="crumb-separator">/</span>
            <span>Execution Pilot</span>
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
                Review exceptions <span className="btn-count">12</span>
              </button>
            </div>
          </div>

          <div className="context-bar">
            <div className="context-item">
              <Database aria-hidden="true" />
              <div>
                <span>Active dataset</span>
                <strong>US Equities · v2024.11.28</strong>
              </div>
              <ChevronDown aria-hidden="true" />
            </div>

            <div className="context-divider" />

            <div className="context-item">
              <Clock3 aria-hidden="true" />
              <div>
                <span>Reporting period</span>
                <strong>
                  {range === "Last 7 days"
                    ? "Last 7 days"
                    : range === "Last 90 days"
                      ? "Last 90 days"
                      : "Nov 01 – Nov 30, 2024"}
                </strong>
              </div>
              <ChevronDown aria-hidden="true" />
            </div>

            <div className="context-spacer" />

            <span className="context-status">
              <span className="status-dot green-dot" /> Data synced 8 min ago
            </span>
          </div>

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
                value="8,426"
                detail="+12.4% vs prior period"
                accent="blue"
                icon={BarChart3}
              />
              <MetricCard
                label="Filled orders"
                value="6,918"
                detail="82.1% fill completion"
                accent="green"
                icon={FileCheck2}
              />
              <MetricCard
                label="Partially filled"
                value="1,104"
                detail="13.1% of total orders"
                accent="amber"
                icon={Activity}
              />
              <MetricCard
                label="Unfilled orders"
                value="404"
                detail="4.8% of total orders"
                accent="slate"
                icon={X}
              />
              <MetricCard
                label="Analysis complete"
                value="6,274"
                detail="74.4% of total · 87.1% eligible"
                accent="blue"
                icon={LineChart}
              />
              <MetricCard
                label="Requires review"
                value="12"
                detail="3 critical · 9 high priority"
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
                  <div className="donut">
                    <div className="donut-center">
                      <strong>87.1%</strong>
                      <span>eligible analyzed</span>
                    </div>
                  </div>
                  <div className="chart-caption">
                    <div>
                      <span className="legend-dot analyzed" /> Analyzed
                      <strong>6,274</strong>
                    </div>
                    <div>
                      <span className="legend-dot failed" /> Failed
                      <strong>928</strong>
                    </div>
                    <div>
                      <span className="legend-dot excluded" /> Excluded
                      <strong>1,224</strong>
                    </div>
                  </div>
                </div>

                <div className="analysis-stats">
                  <div className="analysis-stat">
                    <span>Eligible orders</span>
                    <strong>7,202</strong>
                    <small>85.5% of total orders</small>
                  </div>
                  <div className="analysis-stat">
                    <span>Analysis failures</span>
                    <strong className="text-red">928</strong>
                    <small>
                      12.9% of eligible orders <ArrowDownRight aria-hidden="true" />
                    </small>
                  </div>
                  <div className="failure-note">
                    <AlertCircle aria-hidden="true" />
                    <div>
                      <strong>Primary failure reason</strong>
                      <p>
                        Missing arrival price benchmark <b>· 61.4%</b>
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
                  <p>Median implementation shortfall · basis points</p>
                </div>
                <span className="date-pill">30D <ChevronDown aria-hidden="true" /></span>
              </div>

              <div className="trend-value">
                <strong>-4.8 bps</strong>
                <span className="positive">
                  <ArrowDownRight aria-hidden="true" /> 1.2 bps
                </span>
                <span className="muted-copy">vs prior period</span>
              </div>

              <ExecutionTrendChart />

              <div className="trend-foot">
                <span>
                  <span className="legend-dot analyzed" /> Median IS
                </span>
                <span className="trend-foot-note">
                  Sufficient sample: 6,274 orders
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
                <div className="review-row">
                  <div className="priority-icon critical">
                    <AlertCircle aria-hidden="true" />
                  </div>
                  <div className="review-copy">
                    <strong>Critical slippage outlier</strong>
                    <span>AAPL · Buy 250,000 · 18.4 bps adverse</span>
                  </div>
                  <span className="review-badge critical-badge">Critical</span>
                  <span className="review-owner">Unassigned</span>
                  <button className="row-arrow" type="button" aria-label="Open critical slippage review">
                    <ArrowUpRight aria-hidden="true" />
                  </button>
                </div>

                <div className="review-row">
                  <div className="priority-icon high">
                    <AlertCircle aria-hidden="true" />
                  </div>
                  <div className="review-copy">
                    <strong>Missing benchmark data</strong>
                    <span>3 orders · US Equities · Nov 28</span>
                  </div>
                  <span className="review-badge high-badge">High</span>
                  <span className="review-owner">Unassigned</span>
                  <button className="row-arrow" type="button" aria-label="Open missing benchmark review">
                    <ArrowUpRight aria-hidden="true" />
                  </button>
                </div>

                <div className="review-row">
                  <div className="priority-icon medium">
                    <Clock3 aria-hidden="true" />
                  </div>
                  <div className="review-copy">
                    <strong>Review awaiting evidence</strong>
                    <span>VWAP participation · MSFT · Order #18402</span>
                  </div>
                  <span className="review-badge medium-badge">Medium</span>
                  <span className="review-owner">L. Chen</span>
                  <button className="row-arrow" type="button" aria-label="Open evidence review">
                    <ArrowUpRight aria-hidden="true" />
                  </button>
                </div>
              </div>

              <div className="review-summary">
                <span><strong>12</strong> open reviews</span>
                <span><strong>3</strong> critical / high</span>
                <span><strong>4</strong> unassigned</span>
                <span><strong>5</strong> awaiting evidence</span>
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
                  <strong>Healthy with warnings</strong>
                  <span>Last validated 8 minutes ago</span>
                </div>
              </div>

              <div className="health-items">
                <div>
                  <span>Timestamp coverage</span>
                  <strong>98.6%</strong>
                  <span className="health-good">Within threshold</span>
                </div>
                <div>
                  <span>Instrument coverage</span>
                  <strong>99.2%</strong>
                  <span className="health-good">Within threshold</span>
                </div>
                <div>
                  <span>Missing benchmark data</span>
                  <strong>928 orders</strong>
                  <span className="health-warning">Needs attention</span>
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
              © 2024 Quantara <span className="footer-dot">·</span>{" "}
              <a href="#audit">Audit log</a> <span className="footer-dot">·</span>{" "}
              <a href="#help">Help center</a>
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}