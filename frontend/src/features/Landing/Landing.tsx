
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  BarChart3,
  Check,
  ChevronDown,
  CircleHelp,
  FileCheck2,
  LineChart,
  Menu,
  Moon,
  ShieldCheck,
  Sparkles,
  Sun,
  X,
  Zap,
} from "lucide-react";
import "./Landing.css";

const navItems = ["Platform", "Solutions", "Resources", "Company"];

type Theme = "light" | "dark";

export default function Landing() {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      return localStorage.getItem("quantara-theme") === "dark"
        ? "dark"
        : "light";
    } catch {
      return "light";
    }
  });

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;

    try {
      localStorage.setItem("quantara-theme", theme);
    } catch {
      // The page still works when browser storage is unavailable.
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((current) => (current === "light" ? "dark" : "light"));
  };

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <main className="landing-page">
      <header className="landing-header">
        <Link
          className="landing-brand"
          to="/"
          aria-label="Quantara home"
          onClick={closeMobileMenu}
        >
          <span className="brand-mark">Q</span>
          <span>
            <strong>quantara</strong>
            <small>INSTITUTIONAL INTELLIGENCE</small>
          </span>
        </Link>

        <nav
          className={`landing-nav ${mobileMenuOpen ? "is-open" : ""}`}
          aria-label="Main navigation"
        >
          {navItems.map((item) => (
            <a
              href={`#${item.toLowerCase()}`}
              key={item}
              onClick={closeMobileMenu}
            >
              {item}
              {item !== "Company" && <ChevronDown aria-hidden="true" />}
            </a>
          ))}
        </nav>

        <div className="landing-actions">
          <button
            type="button"
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
            title={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
          >
            {theme === "light" ? (
              <Moon size={17} aria-hidden="true" />
            ) : (
              <Sun size={17} aria-hidden="true" />
            )}
          </button>

          <Link className="sign-in" to="/login">
            Sign in
          </Link>

          <a className="landing-button" href="#demo">
            Request a demo <ArrowRight aria-hidden="true" />
          </a>

          <button
            type="button"
            className="mobile-menu"
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileMenuOpen}
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            {mobileMenuOpen ? (
              <X aria-hidden="true" />
            ) : (
              <Menu aria-hidden="true" />
            )}
          </button>
        </div>
      </header>

      <section className="hero-section">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="live-dot" />
            EXECUTION INTELLIGENCE FOR INSTITUTIONS
          </div>

          <h1>
            Turn every order into a <em>decision advantage.</em>
          </h1>

          <p>
            Quantara gives institutional trading teams the clarity to measure
            execution quality, investigate exceptions, and improve outcomes
            with confidence.
          </p>

          <div className="hero-actions">
            <a className="landing-button large" href="#demo">
              Request a demo <ArrowRight aria-hidden="true" />
            </a>

            <a className="hero-link" href="#platform">
              Explore the platform <ArrowRight aria-hidden="true" />
            </a>
          </div>

          <div className="hero-proof">
            <span>
              <Check aria-hidden="true" /> Built for institutional workflows
            </span>
            <span>
              <Check aria-hidden="true" /> Audit-ready by design
            </span>
          </div>
        </div>

        <div
          className="hero-visual"
          aria-label="Quantara workspace preview"
        >
          <div className="visual-top">
            <span className="mini-brand">
              <span className="brand-mark">Q</span> quantara
            </span>

            <span className="visual-status">
              <span className="green-dot status-dot" /> Live workspace
            </span>
          </div>

          <div className="visual-body">
            <div className="visual-sidebar">
              <span className="visual-active">
                <BarChart3 aria-hidden="true" /> Overview
              </span>
              <span>
                <LineChart aria-hidden="true" /> Analysis
              </span>
              <span>
                <FileCheck2 aria-hidden="true" /> Review queue
              </span>
              <span>
                <ShieldCheck aria-hidden="true" /> Data quality
              </span>
            </div>

            <div className="visual-main">
              <div className="visual-breadcrumb">
                NORTHSTAR CAPITAL / EXECUTION PILOT
              </div>

              <div className="visual-title">
                <div>
                  <span>Workspace Overview</span>
                  <small>Execution intelligence at a glance.</small>
                </div>
                <span className="visual-pill">Last 30 days</span>
              </div>

              <div className="visual-metrics">
                <div>
                  <small>Total orders</small>
                  <strong>8,426</strong>
                  <span className="metric-up">+12.4%</span>
                </div>
                <div>
                  <small>Analysis complete</small>
                  <strong>6,274</strong>
                  <span className="metric-up">74.4%</span>
                </div>
                <div>
                  <small>Requires review</small>
                  <strong>12</strong>
                  <span className="metric-warn">3 critical</span>
                </div>
              </div>

              <div className="visual-chart" aria-label="Illustrative activity chart">
                <div className="chart-line" />
                <div className="chart-bars" aria-hidden="true">
                  <i />
                  <i />
                  <i />
                  <i />
                  <i />
                  <i />
                  <i />
                  <i />
                  <i />
                  <i />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust strip intentionally removed: Quantara is in its pilot stage. */}

      <section className="landing-section" id="platform">
        <div className="section-intro">
          <div className="eyebrow">A CLEARER VIEW OF EXECUTION</div>
          <h2>One workspace for the decisions behind performance.</h2>
          <p>
            Bring order data, benchmarks, review workflows, and research into
            one operational layer your whole team can trust.
          </p>
        </div>

        <div className="feature-grid">
          <article>
            <span className="feature-icon blue">
              <BarChart3 aria-hidden="true" />
            </span>
            <h3>Measure what matters</h3>
            <p>
              See execution quality across orders, desks, brokers, and
              strategies with consistent, defensible metrics.
            </p>
            <a href="#demo">
              Explore analytics <ArrowRight aria-hidden="true" />
            </a>
          </article>

          <article>
            <span className="feature-icon green">
              <ShieldCheck aria-hidden="true" />
            </span>
            <h3>Trust every insight</h3>
            <p>
              Track dataset quality, benchmark coverage, and analysis lineage
              before a result reaches a decision-maker.
            </p>
            <a href="#demo">
              Explore data quality <ArrowRight aria-hidden="true" />
            </a>
          </article>

          <article>
            <span className="feature-icon amber">
              <Sparkles aria-hidden="true" />
            </span>
            <h3>Act on exceptions</h3>
            <p>
              Move from signal to evidence with prioritized reviews, clear
              ownership, and audit-ready decisions.
            </p>
            <a href="#demo">
              Explore review workflows <ArrowRight aria-hidden="true" />
            </a>
          </article>
        </div>
      </section>

      <section className="impact-section">
        <div className="impact-copy">
          <div className="eyebrow">BUILT FOR THE WAY TEAMS WORK</div>
          <h2>Precision without the operational drag.</h2>
          <p>
            Quantara turns fragmented execution data into a shared language
            for traders, quants, operations, and leadership.
          </p>
          <a className="landing-button" href="#demo">
            See Quantara in action <ArrowRight aria-hidden="true" />
          </a>
        </div>

        <div className="impact-list">
          <div>
            <strong>87.1%</strong>
            <span>eligible orders analyzed</span>
          </div>
          <div>
            <strong>4.8 bps</strong>
            <span>median implementation shortfall</span>
          </div>
          <div>
            <strong>12</strong>
            <span>open reviews with clear owners</span>
          </div>
        </div>
      </section>

      <section className="cta-section" id="demo">
        <span className="feature-icon blue">
          <Zap aria-hidden="true" />
        </span>

        <div>
          <div className="eyebrow">START WITH A BETTER SIGNAL</div>
          <h2>Make execution intelligence part of every decision.</h2>
          <p>See how Quantara can fit your team&apos;s workflow.</p>
        </div>

        <a className="landing-button large" href="mailto:hello@quantara.example">
          Talk to our team <ArrowRight aria-hidden="true" />
        </a>
      </section>

      <footer className="landing-footer">
        <Link className="landing-brand" to="/" aria-label="Quantara home">
          <span className="brand-mark">Q</span>
          <span>
            <strong>quantara</strong>
            <small>INSTITUTIONAL INTELLIGENCE</small>
          </span>
        </Link>

        <span>
          © 2026 Quantara. Execution intelligence for institutions.
        </span>

        <div>
          <a href="#platform">Platform</a>
          <a href="#demo">Contact</a>
          <a href="#help">
            <CircleHelp aria-hidden="true" /> Help
          </a>
        </div>
      </footer>
    </main>
  );
}