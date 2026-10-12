import "./Landing.css";
import useScrollReveal from "./useScrollReveal";

const capabilities = [
  {
    number: "01",
    title: "Structured research",
    description:
      "Bring projects, datasets, and research runs into a consistent workspace designed for quantitative workflows.",
    tags: ["Projects", "Datasets", "Workspaces"],
  },
  {
    number: "02",
    title: "Deeper analysis",
    description:
      "Inspect financial metrics and analytical results in a workflow that makes research easier to navigate and understand.",
    tags: ["Returns", "Volatility", "Risk"],
  },
  {
    number: "03",
    title: "Comparable experiments",
    description:
      "Compare completed research runs, identify shared metrics, and understand where results differ.",
    tags: ["Run history", "Metrics", "Comparison"],
  },
];

const workflow = [
  {
    number: "01",
    title: "Organize your inputs",
    description:
      "Structure your research around projects, datasets, and versioned data.",
  },
  {
    number: "02",
    title: "Run your analysis",
    description:
      "Execute supported analyses and keep their results associated with your research workspace.",
  },
  {
    number: "03",
    title: "Review and compare",
    description:
      "Return to saved research and compare completed runs to investigate differences.",
  },
];

function ArrowIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 20 20"
      fill="none"
      className="q-arrow-icon"
    >
      <path
        d="M4.167 10h11.666M10 4.167 15.833 10 10 15.833"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function BrandMark() {
  return (
    <span className="q-brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
      <span />
    </span>
  );
}

function ResearchPreview() {
  const bars = [35, 48, 42, 58, 49, 66, 57, 73, 62, 81, 70, 91, 78, 100];

  return (
    <div
      className="q-preview-shell"
      aria-label="Illustrative Quantara research workspace"
    >
      <div className="q-preview-glow" />

      <div className="q-preview-window">
        <div className="q-window-bar">
          <div className="q-window-brand">
            <BrandMark />
            <span>QUANTARA</span>
          </div>

          <div className="q-window-dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </div>

        <div className="q-preview-body">
          <aside className="q-preview-sidebar">
            <span className="q-sidebar-label">WORKSPACE</span>

            <div className="q-sidebar-item q-sidebar-active">
              <span className="q-sidebar-icon">◫</span>
              Overview
            </div>

            <div className="q-sidebar-item">
              <span className="q-sidebar-icon">⌘</span>
              Research
            </div>

            <div className="q-sidebar-item">
              <span className="q-sidebar-icon">▤</span>
              Datasets
            </div>

            <div className="q-sidebar-item">
              <span className="q-sidebar-icon">⇄</span>
              Comparisons
            </div>

            <div className="q-sidebar-bottom">
              <span className="q-sidebar-label">YOUR WORKSPACE</span>
              <div className="q-workspace-avatar">R</div>
              <span>Research team</span>
            </div>
          </aside>

          <div className="q-preview-main">
            <div className="q-preview-heading">
              <div>
                <span className="q-preview-overline">
                  RESEARCH WORKSPACE
                </span>
                <h3>Research overview</h3>
                <p>Your research, organized.</p>
              </div>

              <span className="q-preview-status">
                <span />
                Workspace
              </span>
            </div>

            <div className="q-metric-grid">
              <div className="q-metric-card">
                <span>Analysis runs</span>
                <strong>24</strong>
                <small>Across your workspace</small>
              </div>

              <div className="q-metric-card">
                <span>Completed</span>
                <strong>18</strong>
                <small>Research records</small>
              </div>

              <div className="q-metric-card">
                <span>Comparisons</span>
                <strong>06</strong>
                <small>Run-to-run reviews</small>
              </div>
            </div>

            <div className="q-chart-card">
              <div className="q-chart-heading">
                <div>
                  <span>RESEARCH ACTIVITY</span>
                  <strong>Analysis landscape</strong>
                </div>

                <span className="q-chart-period">Illustrative</span>
              </div>

              <div className="q-chart">
                <div className="q-chart-grid">
                  <span />
                  <span />
                  <span />
                  <span />
                </div>

                <div className="q-chart-bars" aria-hidden="true">
                  {bars.map((height, index) => (
                    <span
                      key={index}
                      style={{ height: `${height}%` }}
                      className={
                        index === bars.length - 1 ? "q-bar-highlight" : ""
                      }
                    />
                  ))}
                </div>
              </div>

              <div className="q-chart-axis">
                <span>Research activity</span>
                <span>Workspace preview</span>
              </div>
            </div>

            <div className="q-preview-bottom">
              <div>
                <span className="q-mini-indicator" />
                Research history
              </div>

              <span>Organized by workspace</span>
            </div>
          </div>
        </div>
      </div>

      <div className="q-float-note q-float-note-top">
        <span className="q-float-icon">↗</span>
        <div>
          <strong>Research, connected.</strong>
          <span>One structured workspace</span>
        </div>
      </div>

      <div className="q-float-note q-float-note-bottom">
        <span className="q-float-check">✓</span>
        <div>
          <strong>Compare research runs</strong>
          <span>Review metric differences</span>
        </div>
      </div>
    </div>
  );
}

export default function Landing() {
  useScrollReveal();

  return (
    <main className="q-landing">
      <header className="q-header">
        <div className="q-container q-nav">
          <a href="#home" className="q-logo" aria-label="Quantara home">
            <BrandMark />
            <span>QUANTARA</span>
          </a>

          <nav className="q-nav-links" aria-label="Main navigation">
            <a href="#platform">Platform</a>
            <a href="#capabilities">Solutions</a>
            <a href="#workflow">Resources</a>
          </nav>

          <div className="q-nav-actions">
            <a className="q-nav-signin" href="#trust">
              Security
            </a>

            <a
              className="q-button q-button-primary q-nav-cta"
              href="#pilot"
            >
              Request a demo <ArrowIcon />
            </a>
          </div>
        </div>
      </header>

      <section className="q-hero" id="home">
        <div className="q-hero-orb q-hero-orb-one" />
        <div className="q-hero-orb q-hero-orb-two" />

        <div className="q-container q-hero-layout">
          <div className="q-hero-copy">
            <div className="q-hero-badge">
              <span className="q-badge-dot" />
              FINANCIAL INTELLIGENCE, UNIFIED
            </div>

            <h1>
              Your research.
              <br />
              <span>One intelligent</span>
              <br />
              workspace.
            </h1>

            <p className="q-hero-description">
              A structured research workspace for quantitative finance teams.
              Organize datasets, run financial analyses, and compare results
              without losing sight of the work behind them.
            </p>

            <div className="q-hero-actions">
              <a
                className="q-button q-button-primary q-button-large"
                href="#pilot"
              >
                Discuss a pilot <ArrowIcon />
              </a>

              <a className="q-hero-secondary" href="#platform">
                Explore the platform <span>↓</span>
              </a>
            </div>

            <div className="q-hero-proof">
              <div className="q-proof-symbol">◎</div>
              <p>
                <strong>Built for quantitative workflows</strong>
                <span>Research · Analytics · Reproducibility</span>
              </p>
            </div>
          </div>

          <div className="q-hero-visual" id="platform">
            <ResearchPreview />
          </div>
        </div>

        <div className="q-container q-hero-bottom">
          <span>BUILT FOR THE WORK BEHIND FINANCIAL DECISIONS</span>

          <div>
            <span>Quantitative research</span>
            <i />
            <span>Financial analytics</span>
            <i />
            <span>Research comparison</span>
          </div>
        </div>
      </section>

      <section className="q-capabilities q-section" id="capabilities">
        <div className="q-container">
          <div className="q-section-heading" data-reveal>
            <div>
              <span className="q-eyebrow">A MORE CONNECTED WORKFLOW</span>
              <h2>
                Less time navigating.
                <br />
                More time understanding.
              </h2>
            </div>

            <p>
              Financial research is more than a result. It is the data,
              assumptions, analysis, and comparisons behind that result.
              Quantara brings these pieces into a more structured workflow.
            </p>
          </div>

          <div className="q-capability-grid">
            {capabilities.map((item, index) => (
              <article
                className="q-capability-card"
                key={item.number}
                data-reveal
                data-reveal-delay={String(index + 1)}
              >
                <div className="q-capability-top">
                  <span className="q-capability-number">{item.number}</span>
                  <span className="q-capability-arrow">
                    <ArrowIcon />
                  </span>
                </div>

                <h3>{item.title}</h3>
                <p>{item.description}</p>

                <div className="q-tags">
                  {item.tags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="q-workflow q-section" id="workflow">
        <div className="q-container q-workflow-layout">
          <div className="q-workflow-intro" data-reveal>
            <span className="q-eyebrow">FROM INPUTS TO INSIGHT</span>
            <h2>
              A clearer path
              <br />
              through research.
            </h2>

            <p>
              Keep your research workflow organized from the dataset you start
              with to the results you review and compare.
            </p>

            <a className="q-text-link" href="#pilot">
              Explore a pilot <ArrowIcon />
            </a>
          </div>

          <div className="q-workflow-list">
            {workflow.map((step, index) => (
              <article
                className="q-workflow-step"
                key={step.number}
                data-reveal
                data-reveal-delay={String(index + 1)}
              >
                <div className="q-step-number">{step.number}</div>

                <div>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </div>

                <span className="q-step-mark">↗</span>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="q-trust q-section" id="trust">
        <div className="q-container q-trust-panel">
          <div className="q-trust-copy" data-reveal>
            <span className="q-eyebrow">BUILT AROUND RESEARCH CONTEXT</span>
            <h2>
              Results matter.
              <br />
              So does how you got there.
            </h2>

            <p>
              Research should remain understandable after the analysis finishes.
              Quantara connects runs to structured workspaces and supports
              reviewing completed runs side by side.
            </p>
          </div>

          <div className="q-trust-points">
            <div className="q-trust-point" data-reveal data-reveal-delay="1">
              <span className="q-trust-icon">01</span>
              <div>
                <h3>Organized research history</h3>
                <p>Keep research runs associated with their workspace.</p>
              </div>
            </div>

            <div className="q-trust-point" data-reveal data-reveal-delay="2">
              <span className="q-trust-icon">02</span>
              <div>
                <h3>Dataset context</h3>
                <p>Work within projects and versioned datasets.</p>
              </div>
            </div>

            <div className="q-trust-point" data-reveal data-reveal-delay="3">
              <span className="q-trust-icon">03</span>
              <div>
                <h3>Run comparison</h3>
                <p>
                  Inspect shared metrics and differences between completed
                  runs.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="q-pilot-section" id="pilot">
        <div className="q-container">
          <div className="q-pilot-panel">
            <div className="q-pilot-glow" />

            <div className="q-pilot-content" data-reveal>
              <span className="q-eyebrow">START WITH A REAL WORKFLOW</span>
              <h2>
                Let’s solve a research
                <br />
                problem that matters.
              </h2>

              <p>
                We’re shaping Quantara around real quantitative finance
                workflows. Discuss a focused pilot built around your team’s
                research process and operational needs.
              </p>

              <a
                className="q-button q-button-light q-button-large"
                href="#contact"
              >
                Discuss your use case <ArrowIcon />
              </a>
            </div>

            <div className="q-pilot-decoration" aria-hidden="true">
              <BrandMark />
              <span>Q</span>
            </div>
          </div>
        </div>
      </section>

      <footer className="q-footer" id="contact">
        <div className="q-container">
          <div className="q-footer-main" data-reveal>
            <div className="q-footer-brand">
              <a href="#home" className="q-logo">
                <BrandMark />
                <span>QUANTARA</span>
              </a>
              <p>Financial intelligence. Unified.</p>
            </div>

            <div className="q-footer-note">
              <span>BUILT FOR QUANTITATIVE FINANCE</span>
              <p>
                A research workspace designed to bring structure to financial
                analysis and the work behind it.
              </p>
            </div>

            <a className="q-footer-back" href="#home">
              Back to top ↑
            </a>
          </div>

          <div className="q-footer-bottom">
            <span>© {new Date().getFullYear()} Quantara</span>
            <span>Research with context. Decisions with clarity.</span>
          </div>
        </div>
      </footer>
    </main>
  );
}