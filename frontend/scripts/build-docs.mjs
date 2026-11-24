import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { mkdir, readFile, readdir, unlink, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(scriptDirectory, "..");
const repositoryRoot = path.resolve(frontendRoot, "..");
const docsRoot = path.join(repositoryRoot, "docs");
const publicDocsRoot = path.join(frontendRoot, "public", "docs");
const generatedRoot = path.join(frontendRoot, "src", "generated");

const [pagesDocument, shell, pipeline] = await Promise.all([
  readJson(path.join(docsRoot, "site-pages.json")),
  readJson(path.join(docsRoot, "site-shell.json")),
  readJson(
    path.join(repositoryRoot, "backend", "data", "pipeline-status.json"),
  ),
]);

const build = readBuildMetadata();
await mkdir(publicDocsRoot, { recursive: true });
await mkdir(generatedRoot, { recursive: true });
for (const file of await readdir(publicDocsRoot)) {
  if (file.endsWith(".html")) {
    await unlink(path.join(publicDocsRoot, file));
  }
}

await writeFile(
  path.join(generatedRoot, "site-shell.ts"),
  `export const siteShell = ${JSON.stringify(shell, null, 2)} as const;\n`,
  "utf8",
);

for (const page of pagesDocument.pages) {
  await writeFile(
    path.join(publicDocsRoot, `${page.slug}.html`),
    await renderPage(page),
    "utf8",
  );
}

await writeFile(path.join(publicDocsRoot, "index.html"), renderIndex(), "utf8");

async function readJson(file) {
  return JSON.parse(await readFile(file, "utf8"));
}

function readBuildMetadata() {
  const git = (args, fallback) => {
    try {
      return execFileSync("git", args, {
        cwd: repositoryRoot,
        encoding: "utf8",
        stdio: ["ignore", "pipe", "ignore"],
      }).trim();
    } catch {
      return fallback;
    }
  };

  const dirty = git(["status", "--short"], "").length > 0;
  return {
    commit: dirty
      ? "local-pending"
      : git(["rev-parse", "--short", "HEAD"], "local-pending"),
    date: new Date().toISOString().slice(0, 10),
    message: dirty
      ? "Heat and Hot Water implementation"
      : git(["log", "-1", "--pretty=%s"], "local implementation"),
  };
}

async function renderPage(page) {
  const sourceSections = [];
  for (const source of page.sources) {
    const markdown = await readFile(path.join(docsRoot, source), "utf8");
    sourceSections.push(`
      <section class="source-section">
        <div class="source-section__label">Canonical source: <code>${escapeHtml(source)}</code></div>
        ${renderMarkdown(markdown, page.snippets)}
      </section>
    `);
  }

  const pageUrl = `/docs/${page.slug}.html`;
  return documentShell(
    page.title,
    page.lead,
    pageUrl,
    `
      <section class="docs-hero">
        <div class="docs-hero__copy">
          <p class="eyebrow">${escapeHtml(page.eyebrow)}</p>
          <h1>${escapeHtml(page.title)}</h1>
          <p class="lead">${escapeHtml(page.lead)}</p>
          <div class="hero-actions">
            <a class="primary-link" href="/">Open live demo</a>
            <a class="secondary-link" href="/docs/">All documentation</a>
          </div>
        </div>
        ${page.callout ? renderCallout(page.callout) : ""}
      </section>
      ${renderFacts(page.facts)}
      ${page.flow ? renderFlow(page.flow) : ""}
      ${renderVisual(page.visual)}
      ${sourceSections.join("")}
      ${renderRelatedLinks(page.links)}
    `,
  );
}

function renderIndex() {
  const cards = pagesDocument.pages
    .map(
      (page) => `
        <a class="docs-card" href="/docs/${page.slug}.html">
          <span>${escapeHtml(page.eyebrow)}</span>
          <strong>${escapeHtml(page.navLabel)}</strong>
          <p>${escapeHtml(page.lead)}</p>
          <b aria-hidden="true">Read guide →</b>
        </a>
      `,
    )
    .join("");

  return documentShell(
    "Demo documentation",
    "Plain-language guides for the architecture, Strategy model, Microsoft Foundry integration, security, costs, and source path.",
    "/docs/",
    `
      <section class="docs-hero">
        <div class="docs-hero__copy">
          <p class="eyebrow">Public technical guide</p>
          <h1>How the demo works</h1>
          <p class="lead">These pages explain what runs today, what is planned, and where a person must still verify the result.</p>
          <div class="hero-actions">
            <a class="primary-link" href="/">Open live demo</a>
            <a class="secondary-link" href="/health">Service status</a>
          </div>
        </div>
        <div class="docs-hero__aside">
          <span>One rule for every page</span>
          <strong>Strategy owns the number. Foundry explains it.</strong>
          <p>Staff review remains outside the demo. No model can issue a violation or contact a resident.</p>
        </div>
      </section>
      <section class="docs-index" aria-labelledby="guide-list-title">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Six focused guides</p>
            <h2 id="guide-list-title">Choose a layer</h2>
          </div>
          <p>Each guide is generated from the canonical Markdown under <code>/docs</code>.</p>
        </div>
        <div class="docs-card-grid">${cards}</div>
      </section>
    `,
  );
}

function documentShell(title, description, currentUrl, content) {
  const navigation = shell.docsNavigation
    .map(
      (item) =>
        `<a href="${escapeAttribute(item.href)}"${item.href === currentUrl ? ' aria-current="page"' : ""}>${escapeHtml(item.label)}</a>`,
    )
    .join("");
  const footerLinks = shell.footer.links
    .map(
      (item) =>
        `<a href="${escapeAttribute(item.href)}">${escapeHtml(item.label)}</a>`,
    )
    .join("");

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="${escapeAttribute(description)}" />
    <meta name="theme-color" content="#edf6fb" />
    <title>${escapeHtml(title)} | HPD Heat &amp; Hot Water</title>
    <link rel="stylesheet" href="/docs/assets.css" />
    <script src="/docs/theme.js" defer></script>
  </head>
  <body>
    <a class="skip-link" href="#main-content">Skip to content</a>
    <header class="docs-header">
      <a class="brand" href="/">
        <span class="brand-mark" aria-hidden="true">H</span>
        <span>${escapeHtml(shell.brand)}</span>
      </a>
      <nav aria-label="Documentation navigation">${navigation}</nav>
      <button class="theme-button" type="button" data-theme-toggle aria-label="Use dark mode">
        <span data-theme-label>Dark</span>
      </button>
    </header>
    <div class="demo-banner">${escapeHtml(shell.demoPill)}</div>
    <main id="main-content" class="docs-main">${content}</main>
    <footer class="docs-footer">
      <div>
        <strong>${escapeHtml(shell.footer.title)}</strong>
        <p>${escapeHtml(shell.footer.description)}</p>
      </div>
      <nav aria-label="Footer navigation">${footerLinks}</nav>
      <p class="colophon">Last updated ${escapeHtml(build.date)} · ${escapeHtml(build.commit)} · ${escapeHtml(build.message)} · Last updated 0 days ago - content current as of that date.</p>
    </footer>
  </body>
</html>
`;
}

function renderFacts(facts = []) {
  if (!facts.length) return "";
  return `
    <section class="fact-grid" aria-label="Key facts">
      ${facts
        .map(
          (fact) => `
            <article class="fact-card">
              <span>${escapeHtml(fact.label)}</span>
              <strong>${escapeHtml(fact.value)}</strong>
              <p>${escapeHtml(fact.detail)}</p>
            </article>
          `,
        )
        .join("")}
    </section>
  `;
}

function renderFlow(flow) {
  return `
    <section class="doc-flow" aria-labelledby="flow-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">How it moves</p>
          <h2 id="flow-title">One clear path</h2>
        </div>
        <p>Read left to right. Every step keeps a different job.</p>
      </div>
      <ol class="flow-steps">
        ${flow
          .map(
            (item, index) => `
              <li>
                <span>${index + 1}</span>
                <p>${escapeHtml(item)}</p>
              </li>
            `,
          )
          .join("")}
      </ol>
    </section>
  `;
}

function renderCallout(text) {
  return `
    <aside class="docs-hero__aside">
      <span>Current status</span>
      <strong>${escapeHtml(text)}</strong>
    </aside>
  `;
}

function renderVisual(kind) {
  if (kind === "strategy") return renderStrategyVisual();
  if (kind === "costs") return renderCostVisual();
  return "";
}

function renderStrategyVisual() {
  const boroughs = pipeline.borough_metrics;
  const max = Math.max(...boroughs.map((item) => item.distinct_complaints));
  return `
    <section class="rebuild-grid" aria-label="Rebuilt Strategy views">
      <figure class="ui-shot ui-shot--model">
        <figcaption>
          <span>HTML rebuild - not a live screenshot</span>
          <strong>Heat and Hot Water Review Model</strong>
        </figcaption>
        <div class="fake-window">
          <div class="fake-toolbar"><i></i><i></i><i></i><span>Strategy Mosaic</span></div>
          <div class="model-grid">
            <article><b>Borough</b><small>Attribute</small></article>
            <article><b>Building</b><small>Shared building_id</small></article>
            <article><b>Complaint problems</b><small>One problem row</small></article>
            <article><b>Candidate violations</b><small>Needs review</small></article>
            <article><b>311 requests</b><small>Supporting context</small></article>
          </div>
        </div>
      </figure>
      <figure class="ui-shot ui-shot--dashboard">
        <figcaption>
          <span>Rebuilt from pipeline-status.json</span>
          <strong>Heat and Hot Water dashboard</strong>
        </figcaption>
        <div class="fake-window">
          <div class="fake-toolbar"><i></i><i></i><i></i><span>Strategy Dashboard</span></div>
          <div class="mini-kpis">
            <div><span>Distinct complaints</span><strong>${pipeline.kpis.find((item) => item.id === "distinct-complaints")?.value.toLocaleString("en-US") ?? "—"}</strong></div>
            <div><span>Candidate violations</span><strong>${pipeline.kpis.find((item) => item.id === "candidate-violations")?.value.toLocaleString("en-US") ?? "—"}</strong></div>
          </div>
          <div class="mini-bars">
            ${boroughs
              .map(
                (item) => `
                  <div>
                    <span>${escapeHtml(item.borough)}</span>
                    <b style="--bar:${Math.round((item.distinct_complaints / max) * 100)}%"></b>
                    <strong>${item.distinct_complaints.toLocaleString("en-US")}</strong>
                  </div>
                `,
              )
              .join("")}
          </div>
        </div>
      </figure>
      <figure class="ui-shot ui-shot--refresh">
        <figcaption>
          <span>Verified setup</span>
          <strong>Daily refresh subscription</strong>
        </figcaption>
        <div class="fake-window">
          <div class="fake-toolbar"><i></i><i></i><i></i><span>Subscription details</span></div>
          <dl class="refresh-list">
            <div><dt>Schedule</dt><dd>Daily</dd></div>
            <div><dt>Policy</dt><dd>Replace existing data</dd></div>
            <div><dt>Tables</dt><dd>4</dd></div>
            <div><dt>Folders</dt><dd>strategy-buildings, complaints, violations, requests-311</dd></div>
          </dl>
        </div>
      </figure>
    </section>
  `;
}

function renderCostVisual() {
  return `
    <section class="cost-grid" aria-label="Cost drivers">
      <article>
        <span>Usually low for this demo</span>
        <h2>Stored files</h2>
        <p>Four small current CSVs, one manifest, and dated archives.</p>
      </article>
      <article>
        <span>Measure during use</span>
        <h2>Live model calls</h2>
        <p>Input tokens, output tokens, request count, and retry count.</p>
      </article>
      <article>
        <span>Watch as traffic grows</span>
        <h2>App and logs</h2>
        <p>Container starts, request volume, Log Analytics volume, and alert noise.</p>
      </article>
    </section>
  `;
}

function renderRelatedLinks(links = []) {
  if (!links.length) return "";
  return `
    <section class="related-links">
      <div>
        <p class="eyebrow">Official references</p>
        <h2>Read the service details</h2>
      </div>
      <ul>
        ${links
          .map(
            (link) =>
              `<li><a href="${escapeAttribute(link.href)}">${escapeHtml(link.label)}</a></li>`,
          )
          .join("")}
      </ul>
    </section>
  `;
}

function renderMarkdown(markdown, snippets = {}) {
  const lines = markdown.replace(/\r\n?/g, "\n").split("\n");
  const output = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }

    const snippet = line.trim().match(/^\{\{snippet:([^}]+)\}\}$/);
    if (snippet) {
      output.push(renderSnippet(snippets[snippet[1]], snippet[1]));
      index += 1;
      continue;
    }

    const fence = line.match(/^```(.*)$/);
    if (fence) {
      const language = fence[1].trim();
      const code = [];
      index += 1;
      while (index < lines.length && !lines[index].startsWith("```")) {
        code.push(lines[index]);
        index += 1;
      }
      index += 1;
      if (language === "mermaid") {
        output.push(
          '<aside class="doc-note"><strong>Diagram summary</strong><p>The served page uses the plain-language flow above instead of a runtime Mermaid block.</p></aside>',
        );
      } else {
        output.push(renderCode(code.join("\n"), language, "Source example"));
      }
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = Math.min(heading[1].length + 1, 6);
      output.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      index += 1;
      continue;
    }

    if (/^\s*---+\s*$/.test(line)) {
      output.push("<hr />");
      index += 1;
      continue;
    }

    if (
      line.startsWith("|") &&
      index + 1 < lines.length &&
      /^\|?[\s:|-]+\|?\s*$/.test(lines[index + 1])
    ) {
      const headers = splitTableRow(line);
      const rows = [];
      index += 2;
      while (index < lines.length && lines[index].startsWith("|")) {
        rows.push(splitTableRow(lines[index]));
        index += 1;
      }
      output.push(renderTable(headers, rows));
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      const items = [];
      while (index < lines.length && /^[-*]\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^[-*]\s+/, ""));
        index += 1;
      }
      output.push(
        `<ul>${items.map((item) => `<li>${renderInline(item)}</li>`).join("")}</ul>`,
      );
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      const items = [];
      while (index < lines.length && /^\d+\.\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\d+\.\s+/, ""));
        index += 1;
      }
      output.push(
        `<ol>${items.map((item) => `<li>${renderInline(item)}</li>`).join("")}</ol>`,
      );
      continue;
    }

    if (line.startsWith("> ")) {
      const quote = [];
      while (index < lines.length && lines[index].startsWith("> ")) {
        quote.push(lines[index].slice(2));
        index += 1;
      }
      output.push(`<blockquote>${renderInline(quote.join(" "))}</blockquote>`);
      continue;
    }

    const paragraph = [line.trim()];
    index += 1;
    while (
      index < lines.length &&
      lines[index].trim() &&
      !isBlockStart(lines[index]) &&
      !/^```/.test(lines[index])
    ) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    output.push(`<p>${renderInline(paragraph.join(" "))}</p>`);
  }

  return output.join("\n");
}

function isBlockStart(line) {
  return (
    /^(#{1,6})\s+/.test(line) ||
    /^[-*]\s+/.test(line) ||
    /^\d+\.\s+/.test(line) ||
    line.startsWith("|") ||
    line.startsWith("> ") ||
    /^\s*---+\s*$/.test(line) ||
    line.trim().startsWith("{{snippet:")
  );
}

function renderSnippet(config, id) {
  if (!config) {
    throw new Error(`Missing snippet definition for "${id}"`);
  }
  const sourcePath = path.join(repositoryRoot, config.file);
  try {
    const source = readFileSync(sourcePath, "utf8");
    const start = source.indexOf(config.start);
    if (start < 0) throw new Error(`Cannot find start for snippet "${id}"`);
    const end = config.end
      ? source.indexOf(config.end, start + config.start.length)
      : source.length;
    if (end < 0) throw new Error(`Cannot find end for snippet "${id}"`);
    return renderCode(
      source.slice(start, end).trimEnd(),
      config.language,
      config.caption,
      config.file,
    );
  } catch {
    throw new Error(`Cannot read source for snippet "${id}": ${config.file}`);
  }
}

function renderCode(code, language = "text", caption, source = null) {
  return `
    <figure class="code-sample">
      <figcaption>
        <strong>${escapeHtml(caption || "Source example")}</strong>
        ${source ? `<code>${escapeHtml(source)}</code>` : ""}
      </figcaption>
      <pre tabindex="0" aria-label="${escapeAttribute(caption || "Source example")}"><code data-language="${escapeAttribute(language)}">${escapeHtml(code)}</code></pre>
    </figure>
  `;
}

function splitTableRow(line) {
  return line
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function renderTable(headers, rows) {
  return `
    <div class="doc-table-wrap">
      <table>
        <thead><tr>${headers.map((cell) => `<th scope="col">${renderInline(cell)}</th>`).join("")}</tr></thead>
        <tbody>
          ${rows
            .map(
              (row) =>
                `<tr>${row
                  .map((cell) => `<td>${renderInline(cell)}</td>`)
                  .join("")}</tr>`,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderInline(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#96;");
}
