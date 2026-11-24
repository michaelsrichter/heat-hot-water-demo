import { useEffect, useMemo, useState } from "react";
import { getOverview, runReview } from "./api";
import { getBrowserSessionId } from "./session";
import { siteShell } from "./generated/site-shell";
import type {
  DataPipeline,
  Overview,
  PipelineKpi,
  PipelineStep,
  ReviewItem,
  ReviewRun,
} from "./types";
import "./styles.css";

const stateLabels: Record<ReviewItem["state"], string> = {
  new: "Open item",
  carried_forward: "Still open",
  needs_verification: "Needs verification",
};

const pipelineStateLabels: Record<PipelineStep["status"], string> = {
  ready: "Working",
  configured: "Connected",
  blocked: "Blocked",
  snapshot: "Saved snapshot",
  not_configured: "Not connected yet",
  needs_action: "Staff action needed",
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

function KpiCard({ kpi }: { kpi: PipelineKpi }) {
  return (
    <article className="kpi-card">
      <span className="kpi-card__label">{kpi.label}</span>
      <strong>{kpi.value.toLocaleString("en-US")}</strong>
      <span className="kpi-card__unit">{kpi.unit}</span>
      <p>{kpi.why_it_matters}</p>
      <details>
        <summary>How Strategy counts this</summary>
        <p>{kpi.definition}</p>
        <code>{kpi.strategy_object}</code>
      </details>
    </article>
  );
}

function OpenWorkDashboard({ pipeline }: { pipeline: DataPipeline }) {
  const openKpis = pipeline.kpis.filter((kpi) =>
    [
      "unresolved-complaints",
      "unresolved-candidate-violations",
      "buildings-with-candidate-violations",
    ].includes(kpi.id),
  );
  const contextKpis = pipeline.kpis.filter(
    (kpi) => !openKpis.some((openKpi) => openKpi.id === kpi.id),
  );

  return (
    <section className="open-work" aria-labelledby="open-work-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Today&apos;s supervisor view</p>
          <h2 id="open-work-title">
            How much heat and hot-water work is still open?
          </h2>
          <p className="section-copy">
            These are the latest counts from Strategy, refreshed on{" "}
            <strong>{formatDate(pipeline.strategy_as_of)}</strong>. Strategy
            defines each count. Foundry does not recalculate it.
          </p>
        </div>
        <span className="connection-badge">Latest Strategy snapshot</span>
      </div>

      <div className="open-work__explain">
        <div className="open-work__message">
          <strong>Start with these two queues.</strong>
          <span>
            An <b>unresolved complaint</b> is a distinct complaint Strategy
            still marks OPEN. An <b>unresolved candidate violation</b> is a
            possible violation Strategy still marks Open and staff must verify.
          </span>
        </div>
        <div className="open-work__foundry">
          <strong>What Foundry adds</strong>
          <span>
            It reads the selected building records, these Strategy KPIs, and
            current HPD guidance. Then it suggests what to check next.
          </span>
        </div>
      </div>

      <p className="strategy-source-status">
        <strong>Where the numbers come from:</strong>{" "}
        {pipeline.strategy_source === "strategy-mosaic-mcp-mock"
          ? "Strategy MCP demo mode. These numbers come from the latest governed Strategy export, wrapped in a clearly labeled mock MCP response."
          : pipeline.strategy_source === "strategy-mosaic-mcp"
            ? "The page uses a live, read-only Strategy Mosaic MCP query."
            : "Strategy Mosaic is the source of truth. This page uses its latest governed export; live MCP is waiting on model access."}
      </p>

      {pipeline.strategy_mcp_trace && (
        <details className="mcp-trace">
          <summary>Show the simulated Strategy MCP conversation</summary>
          <div className="mcp-trace__notice">
            <strong>Demo response — not a live MCP call.</strong>
            <span>{pipeline.strategy_mcp_trace.notice}</span>
          </div>
          <dl className="mcp-trace__meta">
            <div>
              <dt>Project</dt>
              <dd>{pipeline.strategy_mcp_trace.project}</dd>
            </div>
            <div>
              <dt>Model</dt>
              <dd>{pipeline.strategy_mcp_trace.model}</dd>
            </div>
          </dl>
          <ol className="mcp-trace__steps">
            {pipeline.strategy_mcp_trace.trace.map((step, index) => (
              <li key={step.tool}>
                <span>{index + 1}</span>
                <div>
                  <strong>{step.tool}</strong>
                  <p>{step.purpose}</p>
                  <details>
                    <summary>Request and expected response</summary>
                    <pre>{JSON.stringify(step.request, null, 2)}</pre>
                    <p className="mcp-trace__response">
                      {step.response_preview}
                    </p>
                  </details>
                </div>
              </li>
            ))}
          </ol>
        </details>
      )}

      <div className="kpi-grid open-work__kpis">
        {openKpis.map((kpi) => (
          <KpiCard key={kpi.id} kpi={kpi} />
        ))}
      </div>

      <div className="borough-breakdown">
        <div>
          <p className="eyebrow">Open work by borough</p>
          <h3>Compare Strategy totals with the unresolved queue.</h3>
          <p>
            The first two columns match the Strategy dashboard. The last two
            show the unresolved records a supervisor can prioritize.
          </p>
        </div>
        <div className="borough-table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Borough</th>
                <th scope="col">Distinct complaints</th>
                <th scope="col">Candidate violations</th>
                <th scope="col">Unresolved complaints</th>
                <th scope="col">Unresolved candidate violations</th>
              </tr>
            </thead>
            <tbody>
              {pipeline.borough_metrics.map((metric) => (
                <tr key={metric.borough}>
                  <th scope="row">{metric.borough}</th>
                  <td>{metric.distinct_complaints.toLocaleString("en-US")}</td>
                  <td>{metric.candidate_violations.toLocaleString("en-US")}</td>
                  <td>
                    {metric.unresolved_complaints.toLocaleString("en-US")}
                  </td>
                  <td>
                    {metric.unresolved_candidate_violations.toLocaleString(
                      "en-US",
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <details className="metric-library">
        <summary>See the rest of the Strategy KPI definitions</summary>
        <div className="kpi-grid">
          {contextKpis.map((kpi) => (
            <KpiCard key={kpi.id} kpi={kpi} />
          ))}
        </div>
      </details>

      <details className="strategy-source-note">
        <summary>Where these numbers come from</summary>
        <p>
          Strategy Mosaic owns the KPI names, formulas, dates, and
          relationships. This demo reads the latest governed export from Azure
          Data Lake Storage. A live Strategy Mosaic MCP connection is the
          intended next source, but it is not authenticated in this demo.
        </p>
        <p>
          Current connection:{" "}
          <code>
            {pipeline.strategy_source === "strategy-mosaic-mcp"
              ? "Strategy Mosaic MCP"
              : "Strategy Mosaic governed snapshot"}
          </code>
          . MCP status: <code>{pipeline.strategy_mcp_status}</code>.
        </p>
      </details>
    </section>
  );
}

function ProcessFlow({ pipeline }: { pipeline: DataPipeline }) {
  return (
    <section
      className="process-flow"
      id="how-it-works"
      aria-labelledby="process-title"
    >
      <div className="section-heading process-heading">
        <div>
          <p className="eyebrow">From report to follow-up</p>
          <h2 id="process-title">
            How a complaint becomes a clear review list
          </h2>
          <p className="section-copy">
            NYC public records are counted in Strategy Mosaic. The demo
            assistant can explain those governed facts, but it cannot change the
            numbers or decide an enforcement action.
          </p>
        </div>
        <div className="architecture-label">
          <span>Number definitions</span>
          <strong>Strategy Mosaic</strong>
          <small>One shared meaning across the dashboard and the app</small>
        </div>
      </div>

      <ol className="process-steps">
        {pipeline.steps.map((step) => (
          <li key={step.id}>
            <div className="process-card__top">
              <span className="process-number">{step.order}</span>
              <span className={`process-state process-state--${step.status}`}>
                {pipelineStateLabels[step.status]}
              </span>
            </div>
            <h3>{step.title}</h3>
            <p>{step.detail}</p>
            <div className="process-owner">
              <span>{step.owner}</span>
              <code>{step.artifact}</code>
            </div>
          </li>
        ))}
      </ol>

      <div className="pipeline-route" aria-label="Data route">
        <span>NYC public records</span>
        <b aria-hidden="true">→</b>
        <span>Azure storage</span>
        <b aria-hidden="true">→</b>
        <span>Strategy Mosaic</span>
        <b aria-hidden="true">→</b>
        <span>Foundry IQ briefing</span>
        <b aria-hidden="true">→</b>
        <span>HPD staff review</span>
      </div>
    </section>
  );
}

function DemoStory() {
  return (
    <section className="demo-story" aria-labelledby="demo-story-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Microsoft AI + Strategy</p>
          <h2 id="demo-story-title">
            The right answer starts with the right facts
          </h2>
          <p className="section-copy">
            Strategy keeps the numbers consistent. Microsoft Foundry explains
            the evidence. Housing teams receive a building-level plan they can
            verify and own.
          </p>
        </div>
      </div>
      <ol className="story-steps">
        <li>
          <span className="story-step-number">1</span>
          <p className="eyebrow">Define in Strategy</p>
          <h3>Everyone uses one metric meaning</h3>
          <p>
            Mosaic shows where the data came from and exactly how complaints,
            violations, buildings, and dates are counted.
          </p>
        </li>
        <li>
          <span className="story-step-number">2</span>
          <p className="eyebrow">Explain with Microsoft Foundry</p>
          <h3>AI reads the governed facts and guidance</h3>
          <p>
            The assistant identifies what is known, what is missing, and what a
            staff member should check next.
          </p>
        </li>
        <li>
          <span className="story-step-number">3</span>
          <p className="eyebrow">Route to an owner</p>
          <h3>Each building gets a practical follow-up plan</h3>
          <p>
            Borough owners can work smaller neighborhood areas when the volume
            is too large for one queue.
          </p>
        </li>
      </ol>
    </section>
  );
}

function ReviewCard({ item }: { item: ReviewItem }) {
  return (
    <article className="review-card">
      <div className="review-card__top">
        <div>
          <p className="eyebrow">
            {item.service_area} · Synthetic practice record
          </p>
          <h3>{item.building_label}</h3>
        </div>
        <span className={`state state--${item.state}`}>
          {stateLabels[item.state]}
        </span>
      </div>
      <p className="lead-copy">{item.trigger}</p>
      <dl className="facts">
        {item.observed_facts.map((fact) => (
          <div key={fact}>
            <dt>What the record shows</dt>
            <dd>{fact}</dd>
          </div>
        ))}
      </dl>
      {item.unknowns.length > 0 && (
        <div className="unknowns">
          <strong>What still needs checking</strong>
          <ul>
            {item.unknowns.map((unknown) => (
              <li key={unknown}>{unknown}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="follow-up">
        <strong>Suggested follow-up:</strong> {item.suggested_follow_up}
      </p>
      <div className="assignment">
        <strong>Responsible team</strong>
        <span>{item.owner_team}</span>
      </div>
      <ol className="action-list">
        {item.action_plan.map((action) => (
          <li key={action}>{action}</li>
        ))}
      </ol>
      <p className="decision-note">
        A staff member must verify the source and choose the next official
        action.
      </p>
      <div className="citations">
        {item.citations.map((citation) => (
          <a
            href={citation.url}
            key={`${citation.scope}-${citation.title}`}
            target="_blank"
            rel="noreferrer"
          >
            {citation.scope === "data"
              ? "View source record"
              : "Read official guidance"}
            <span className="sr-only">: {citation.title}</span>
          </a>
        ))}
      </div>
    </article>
  );
}

function Results({
  run,
  selectedArea,
}: {
  run: ReviewRun;
  selectedArea: string;
}) {
  const counts = useMemo(
    () => ({
      new: run.items.filter((item) => item.state === "new").length,
      carried: run.items.filter((item) => item.state === "carried_forward")
        .length,
      verify: run.items.filter((item) => item.state === "needs_verification")
        .length,
    }),
    [run.items],
  );
  const ownerGroups = useMemo(() => {
    const groups = new Map<
      string,
      {
        serviceArea: string;
        ownerTeam: string;
        items: ReviewItem[];
      }
    >();
    for (const item of run.items) {
      const key = `${item.service_area}:${item.owner_team}`;
      const group = groups.get(key) ?? {
        serviceArea: item.service_area,
        ownerTeam: item.owner_team,
        items: [],
      };
      group.items.push(item);
      groups.set(key, group);
    }
    return [...groups.values()];
  }, [run.items]);

  return (
    <section className="results" aria-labelledby="results-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Foundry result</p>
          <h2 id="results-title">
            Next steps for{" "}
            {selectedArea === "all" ? "all practice areas" : selectedArea}
          </h2>
          <p>
            Strategy&apos;s rule selected <strong>{run.strategy_count}</strong>{" "}
            practice {run.strategy_count === 1 ? "building" : "buildings"}.
            Foundry prepared <strong>{run.eligible_count}</strong>{" "}
            {run.eligible_count === 1 ? "record" : "records"} for staff to
            verify.
          </p>
        </div>
        <div className="result-summary" aria-label="Follow-up list summary">
          <span>{counts.new} new</span>
          <span>{counts.carried} still open</span>
          <span>{counts.verify} to verify</span>
        </div>
      </div>

      <ol className="review-steps">
        {run.steps.map((step) => (
          <li key={step}>
            <span aria-hidden="true">✓</span>
            {step}
          </li>
        ))}
      </ol>

      {run.briefing && (
        <section className="briefing-card" aria-labelledby="briefing-title">
          <div>
            <p className="eyebrow">
              {run.briefing.mode === "practice"
                ? "Foundry practice briefing"
                : "Foundry IQ briefing"}
            </p>
            <h2 id="briefing-title">What Foundry recommends checking next</h2>
            <p className="briefing-provider">{run.briefing.provider}</p>
          </div>
          <div className="briefing-text">
            {run.briefing.text.split("\n").map((line, index) => (
              <p
                key={`${line}-${index}`}
                className={line.startsWith("- ") ? "briefing-bullet" : ""}
              >
                {line}
              </p>
            ))}
          </div>
          <div className="citations">
            {run.briefing.citations.map((citation) => (
              <a
                href={citation.url}
                key={citation.url}
                target="_blank"
                rel="noreferrer"
              >
                {citation.scope === "data"
                  ? "Open practice record"
                  : citation.title}
              </a>
            ))}
          </div>
        </section>
      )}

      <section className="owner-plan" aria-labelledby="owner-plan-title">
        <div className="owner-plan__heading">
          <p className="eyebrow">Owner-ready worklist</p>
          <h2 id="owner-plan-title">Action plan by service area</h2>
          <p>
            Each plan names the evidence to check and the responsible role. It
            does not send an official action.
          </p>
        </div>
        <div className="owner-plan-grid">
          {ownerGroups.map((group) => (
            <article
              className="owner-plan-card"
              key={`${group.serviceArea}-${group.ownerTeam}`}
            >
              <p className="eyebrow">{group.serviceArea}</p>
              <h3>{group.ownerTeam}</h3>
              {group.items.map((item) => (
                <div className="building-plan" key={item.building_id}>
                  <strong>{item.building_label}</strong>
                  <span className={`state state--${item.state}`}>
                    {stateLabels[item.state]}
                  </span>
                  <ol>
                    {item.action_plan.map((action) => (
                      <li key={action}>{action}</li>
                    ))}
                  </ol>
                </div>
              ))}
            </article>
          ))}
        </div>
      </section>

      <div className="review-grid">
        {run.items.map((item) => (
          <ReviewCard item={item} key={item.building_id} />
        ))}
      </div>
    </section>
  );
}

export default function App() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [selectedScenario, setSelectedScenario] = useState("");
  const [selectedArea, setSelectedArea] = useState("all");
  const [run, setRun] = useState<ReviewRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">(
    document.documentElement.dataset.theme === "dark" ? "dark" : "light",
  );

  useEffect(() => {
    getOverview()
      .then((next) => {
        setOverview(next);
        setSelectedScenario(next.scenarios.at(-1)?.id ?? "");
      })
      .catch((cause: unknown) => {
        setError(
          cause instanceof Error
            ? cause.message
            : "The demo could not load its public-record summary.",
        );
      });
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  async function startReview() {
    setLoading(true);
    setError("");
    setRun(null);
    try {
      setRun(
        await runReview(
          selectedScenario,
          getBrowserSessionId(),
          selectedArea === "all" ? undefined : selectedArea,
        ),
      );
    } catch (cause: unknown) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The practice follow-up list could not be prepared.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (!overview) {
    return (
      <main className="loading-page">
        <div className="skeleton skeleton--title" />
        <div className="skeleton skeleton--wide" />
        <div className="skeleton-grid">
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
        {error && <p className="error">{error}</p>}
      </main>
    );
  }

  const current =
    overview.scenarios.find((scenario) => scenario.id === selectedScenario) ??
    overview.scenarios[0];

  return (
    <>
      <header className="site-header">
        <a className="brand" href="#top">
          <span className="brand-mark" aria-hidden="true">
            H
          </span>
          HPD Heat &amp; Hot Water
        </a>
        <nav aria-label="Main navigation">
          {siteShell.demoNavigation.map((item) => (
            <a
              className={item.href === "/docs/" ? "docs-nav-link" : undefined}
              href={item.href}
              key={item.href}
            >
              {item.label}
            </a>
          ))}
          <button
            type="button"
            className="theme-button"
            aria-label={`Use ${theme === "light" ? "dark" : "light"} mode`}
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          >
            {theme === "light" ? "Dark" : "Light"}
          </button>
        </nav>
      </header>

      <main id="top">
        <section className="hero">
          <p className="demo-pill">
            NYC housing response demo · Not an official city service
          </p>
          <div className="hero-grid">
            <div>
              <h1>
                Turn heat and hot-water complaints into clear next actions.
              </h1>
              <p className="hero-copy">
                This demo shows how Housing Preservation and Development staff
                can review complaints, check related violations, and prepare a
                documented follow-up. Strategy defines the facts. Microsoft
                Foundry explains the evidence. HPD teams verify and act.
              </p>
              <div className="hero-actions">
                <a className="primary-link" href="#review">
                  Try the practice review
                </a>
                <a className="secondary-link" href="#overview">
                  See today&apos;s open work
                </a>
              </div>
            </div>
            <div className="hero-note">
              <span className="warm-icon" aria-hidden="true">
                ●
              </span>
              <strong>A review aid, not an enforcement decision.</strong>
              <span>
                The app does not contact residents, close cases, or decide a
                violation. A housing staff member checks the source and chooses
                what happens next.
              </span>
            </div>
          </div>
        </section>

        <DemoStory />

        <div id="overview">
          <OpenWorkDashboard pipeline={overview.data_pipeline} />

          <div className="strategy-callout">
            <div>
              <p className="eyebrow">Why Strategy matters here</p>
              <h3>One metric has one approved meaning.</h3>
              <p>
                A complaint can include several problem rows. A violation can
                appear without being caused by a complaint. Strategy keeps those
                grains and relationships separate so staff see the right count
                in every screen.
              </p>
            </div>
            <dl>
              <div>
                <dt>Semantic model</dt>
                <dd>{overview.data_pipeline.strategy_model}</dd>
              </div>
              <div>
                <dt>Shared dashboard</dt>
                <dd>{overview.data_pipeline.strategy_dashboard}</dd>
              </div>
              <div>
                <dt>Refresh</dt>
                <dd>Four ADLS tables, scheduled daily</dd>
              </div>
            </dl>
          </div>
        </div>

        <ProcessFlow pipeline={overview.data_pipeline} />

        <section className="review" id="review" aria-labelledby="review-title">
          <div className="review-intro">
            <p className="eyebrow">Ask Foundry for help</p>
            <h2 id="review-title">Choose your area and get a next-step plan</h2>
            <p className="section-copy">
              This practice queue uses synthetic building records. Strategy
              supplies the KPI rules and unresolved counts. Foundry reads the
              selected records and official guidance.
            </p>
            <ol className="mini-steps">
              <li>
                <span>1</span> Pick the borough or neighborhood you own.
              </li>
              <li>
                <span>2</span> Foundry finds missing facts and possible next
                steps.
              </li>
              <li>
                <span>3</span> A staff member verifies the plan before acting.
              </li>
            </ol>
          </div>
          <div className="scenario-area">
            <label className="area-field">
              <span>Your borough or neighborhood</span>
              <select
                aria-label="Your borough or neighborhood"
                value={selectedArea}
                onChange={(event) => {
                  setSelectedArea(event.target.value);
                  setRun(null);
                }}
              >
                <option value="all">All practice areas</option>
                {overview.service_areas.map((area) => (
                  <option value={area} key={area}>
                    {area}
                  </option>
                ))}
              </select>
              <small>
                Practice queue: {current.title}. Source snapshot{" "}
                {formatDate(current.source_snapshot_date)}.
              </small>
            </label>
            <div className="foundry-explainer">
              <strong>What Foundry receives</strong>
              <ul>
                <li>The selected synthetic building records</li>
                <li>Strategy KPI definitions and unresolved counts</li>
                <li>The official HPD heat and hot-water guidance link</li>
              </ul>
              <p>
                Foundry cannot change Strategy counts or take an official
                action.
              </p>
            </div>
            <button
              className="primary-button"
              type="button"
              onClick={startReview}
              disabled={loading || !current}
            >
              {loading
                ? "Foundry is preparing the plan…"
                : "Ask Foundry for a next-step plan"}
            </button>
            <p className="practice-reminder">
              Practice only. No resident data is shown. No official action is
              sent.
            </p>
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
          </div>
        </section>

        {loading && (
          <section className="working" aria-live="polite">
            <p className="eyebrow">Review in progress</p>
            <h2>Checking the saved practice records…</h2>
            <p>Separating facts, unknowns, and official guidance.</p>
            <div className="skeleton-grid">
              <div className="skeleton" />
              <div className="skeleton" />
              <div className="skeleton" />
            </div>
          </section>
        )}

        {run && <Results run={run} selectedArea={selectedArea} />}

        <section className="limits" id="limits" aria-labelledby="limits-title">
          <div>
            <p className="eyebrow">Important limits</p>
            <h2 id="limits-title">What this demo can and cannot tell you</h2>
          </div>
          <ul>
            {overview.source_limitations.map((limit) => (
              <li key={limit}>{limit}</li>
            ))}
          </ul>
          <details>
            <summary>How Strategy and Foundry work together</summary>
            <p>
              Strategy Mosaic owns each metric definition, date, and
              relationship. The Foundry assistant reads those approved values
              and official HPD guidance. It does not recalculate the metric from
              raw files.
            </p>
            <p>
              Rule version: <code>{overview.rule_version}</code>. Strategy:{" "}
              <code>{overview.strategy_connection}</code>. Foundry IQ:{" "}
              <code>{overview.foundry_connection}</code>.
            </p>
          </details>
          <details>
            <summary>Why every follow-up needs a person</summary>
            <p>{overview.rule_description}</p>
            <p>
              A recorded date, complaint count, or violation status does not
              prove that heat or hot water was restored. Urgent HPD procedures
              still apply.
            </p>
          </details>
          <details>
            <summary>Technical details</summary>
            <p>
              Public NYC files are written to ADLS Gen2. Strategy imports four
              current table folders and refreshes them on a schedule. The app
              receives a safe process manifest and synthetic practice records.
            </p>
            <p>
              Storage account:{" "}
              <code>{overview.data_pipeline.storage_account}</code>. Container:{" "}
              <code>{overview.data_pipeline.container}</code>. Manifest:{" "}
              <code>{overview.data_pipeline.manifest_path}</code>.
            </p>
          </details>
        </section>
      </main>

      <footer>
        <div>
          <strong>{siteShell.footer.title}</strong>
          <p>{siteShell.footer.description}</p>
        </div>
        <nav aria-label="Footer navigation">
          {siteShell.footer.links.map((item) => (
            <a href={item.href} key={item.label}>
              {item.label}
            </a>
          ))}
          <a href="#top">Back to top</a>
        </nav>
        <p className="colophon">
          Last updated {__BUILD_DATE__} · {__BUILD_COMMIT__} ·{" "}
          {__BUILD_MESSAGE__} · Content is current as of this date.
        </p>
      </footer>
    </>
  );
}
